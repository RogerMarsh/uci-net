# engine.py
# Copyright 2015 Roger Marsh
# License: See LICENSE.TXT (BSD licence)

"""Collate analysis from a chess engine.

The chess engine must support the Universal Chess Interface (UCI).

"""

from collections import namedtuple, deque
import re
from copy import deepcopy


class EngineError(Exception):
    pass


class CommandsToEngine(object):
    """The names of commands sent to engines."""
    uci = 'uci'
    debug = 'debug'
    isready = 'isready'
    setoption = 'setoption'
    register = 'register'
    ucinewgame = 'ucinewgame'
    position = 'position'
    go = 'go'
    stop = 'stop'
    ponderhit = 'ponderhit'
    quit_ = 'quit'
    start = 'start'


class GoSubCommands(object):
    """The names of sub-commands of the go command sent to engines."""
    searchmoves = 'searchmoves'
    ponder = 'ponder'
    wtime = 'wtime'
    btime = 'btime'
    winc = 'winc'
    binc = 'binc'
    movestogo = 'movestogo'
    depth = 'depth'
    nodes = 'nodes'
    mate = 'mate'
    movetime = 'movetime'
    infinite = 'infinite'


class PositionSubCommands(object):
    """The names of sub-commands of the position command sent to engines."""
    fen = 'fen'
    startpos = 'startpos'
    moves = 'moves'


class SetoptionSubCommands(object):
    """The names of sub-commands of the setoption command sent to engines."""
    name = 'name'
    value = 'value'


class CommandsFromEngine(object):
    """The names of commands sent by engines."""
    id_ = 'id'
    uciok = 'uciok'
    readyok = 'readyok'
    bestmove = 'bestmove'
    copyprotection = 'copyprotection'
    registration = 'registration'
    info = 'info'
    option = 'option'

    all_ = frozenset((id_,
                      uciok,
                      readyok,
                      bestmove,
                      copyprotection,
                      registration,
                      info,
                      option))
    terminators = frozenset((uciok,
                             readyok,
                             bestmove,
                             copyprotection,
                             registration))

    # Regular expression to parse text from engine for command
    # re = '\s+(name|type|default|min|max|var)\s+'
    cfere = re.compile('|'.join(all_).join(('(?:\A|\s+)(', ')(?:\s+|\Z)')))

    @staticmethod
    def parse_command(text):
        """Return name of command from text or None if no command found.

        The first word matching a command name is treated as the command, but
        further words matching a command name are assumed to be sub-commands
        or part of a value.

        UCI does not define any such sub-commands but only advises against
        values which contain command or sub-command names.

        """
        cfe = CommandsFromEngine
        cfesplit = [t.strip() for t in cfe.cfere.split(text, maxsplit=1)]

        # A valid command gives exactly:
        # [ <junk>|'' , <command> , <parameters>|'' ]
        if len(cfesplit) != 3:
            return None
        return cfesplit[1]


class IdParameters(object):
    """The names of parameters in the id command."""
    name = 'name'
    author = 'author'

    all_ = frozenset((name, author))

    # Regular expression to parse option command
    # re = '(?<= )(name|author)\s+'
    ipre = re.compile('|'.join(all_).join(('(?<= )(', ')\s+')))

    @staticmethod
    def parse_id(text):
        """Return value of id parameter extracted from text.

        The UCI specification does not say multiple parameters cannot be put
        in one id command.  However the values of the parameters are not under
        the control of the specification, and the examples use one parameter
        per command.  So this parser assumes one parameter per command.

        """
        ip = IdParameters
        ipsplit = [t.strip() for t in ip.ipre.split(text, maxsplit=1)]

        # '<junk> id <parameter name> ... is fine but
        # '<junk> id <junk> <parameter name> ... is not.
        if ipsplit[0].split()[-1] != CommandsFromEngine.id_:
            return {}

        o = {}
        for p, v in [ipsplit[i:i+2] for i in range(1, len(ipsplit), 2)]:
            o[p] = v
        return o


class OptionParameters(object):
    """The names of parameters in the option command.

    Quoted from the UCI specification (downloaded 9 August 2015):

    @@@
    This command tells the GUI which parameters can be changed in the engine.
    This should be sent once at engine startup after the "uci" and the "id"
    commands if any parameter can be changed in the engine.
    ...
    One string will be sent for each parameter.
    @@@

    and

    @@@
    all command strings the engine receives will end with '\n', also all
    commands the GUI receives should end with '\n',
    @@@.

    The interpretation is only one 'name' parameter is allowed in a command.

    Commands something like 'option name ... name ... name ...', recommended by
    '... This should be sent once ...', are not supported.  Note it is trivial
    to implement support for such commands.

    The gnuchess and stockfish engines, for example, use this interpretation.

    """
    name = 'name'
    type_ = 'type'
    default = 'default'
    min_ = 'min'
    max_ = 'max'
    var = 'var'
    all_ = frozenset((name, type_, default, min_, max_, var))

    # The multi-value parameters
    multi = frozenset((var,))

    # Regular expression to parse option command
    # re = '(?<= )(name|type|default|min|max|var)\s+'
    opre = re.compile('|'.join(all_).join(('(?<= )(', ')\s+')))

    @staticmethod
    def parse_option(text):
        """Recturn dict of option parameters extracted from text."""
        op = OptionParameters
        opsplit = [t.strip() for t in op.opre.split(text)]

        # '<junk> option <parameter name> ... is fine but
        # '<junk> option <junk> <parameter name> ... is not.
        if opsplit[0].split()[-1] != CommandsFromEngine.option:
            return {}

        # Verify option command is not ambiguous only.
        for p in op.name, op.type_, op.default, op.min_, op.max_:
            if opsplit.count(p) > 1:
                return {}

        o = {}
        for p, v in [opsplit[i:i+2] for i in range(1, len(opsplit), 2)]:
            if p in op.multi:
                o.setdefault(p, []).append(v)
            else:
                o[p] = v
        return o


class OptionTypes(object):
    """The values of type and <Type> in the <Type>Option namedtuples."""
    button = 'button'
    check = 'check'
    combo = 'combo'
    spin = 'spin'
    string = 'string'


ButtonOption = namedtuple('ButtonOption', ('name', 'type'))
CheckOption = namedtuple('CheckOption', ('name', 'type', 'default'))
ComboOption = namedtuple('ComboOption', ('name', 'type', 'default', 'var'))
SpinOption = namedtuple('SpinOption', ('name', 'type', 'default', 'min', 'max'))
StringOption = namedtuple('StringOption', ('name', 'type', 'default'))


class ReservedOptionNames(object):
    """The names of options defined in UCI specification.

    Any names starting 'UCI_' not in type_ are invalid and thus ignored.

    Other names except the first six in type_ (not starting 'UCI_') are engine
    specific.

    """
    _false = 'false'
    _true = 'true'
    _check_values = frozenset((_true, _false))

    clear_hash = 'Clear Hash'
    empty_string = '<empty>'
    reserved_prefix = 'UCI_'
    Hash = 'Hash'
    NalimovPath = 'NalimovPath'
    NalimovCache = 'NalimovCache'
    Ponder = 'Ponder'
    OwnBook = 'OwnBook'
    MultiPV = 'MultiPV'
    UCI_ShowCurrLine = 'UCI_ShowCurrLine'
    UCI_ShowRefutations = 'UCI_ShowRefutations'
    UCI_LimitStrength = 'UCI_LimitStrength'
    UCI_Elo = 'UCI_Elo'
    UCI_AnalyseMode = 'UCI_AnalyseMode'
    UCI_Opponent = 'UCI_Opponent'
    UCI_EngineAbout = 'UCI_EngineAbout'
    UCI_ShredderbasesPath = 'UCI_ShredderbasesPath'
    UCI_SetPositionValue = 'UCI_SetPositionValue'
    UCI_Chess960 = 'UCI_Chess960'
    type_ = {
        Hash: OptionTypes.spin,
        NalimovPath: OptionTypes.string,
        NalimovCache: OptionTypes.spin,
        Ponder: OptionTypes.check,
        OwnBook: OptionTypes.check,
        MultiPV: OptionTypes.spin,
        UCI_ShowCurrLine: OptionTypes.check,
        UCI_ShowRefutations: OptionTypes.check,
        UCI_LimitStrength: OptionTypes.check,
        UCI_Elo: OptionTypes.spin,
        UCI_AnalyseMode: OptionTypes.check,
        UCI_Opponent: OptionTypes.string,
        UCI_EngineAbout: OptionTypes.string,
        UCI_ShredderbasesPath: OptionTypes.string,
        UCI_SetPositionValue: OptionTypes.string,
        UCI_Chess960: OptionTypes.check,
        }
    default = {
        MultiPV: '1',
        UCI_ShowCurrLine: _false,
        UCI_ShowRefutations: _false,
        UCI_LimitStrength: _false,
        }

    @staticmethod
    def is_invalid_defined_option(
        name=None, type_=None, default=None, min_=None, max_=None, var=None):
        """Return True if arguments are an invalid for a UCI defined option."""
        ron = ReservedOptionNames
        if name not in ron.type_:
            if name.startswith(ron.reserved_prefix):
                return True
        if type_ != ron.type_[name]:
            return True
        if name in ron.default:
            if default != ron.default[default]:
                return True
        return False


def option(name=None, type_=None, default=None, min_=None, max_=None, var=None):
    """Return a <Type>Option instance for type_, or None if arguments invalid.

    UCI usually just ignores invalid options, so do the same here.

    """
    if not isinstance(name, str):
        return None
    if ReservedOptionNames.isinvalid_defined_option(
        name=name, type_=type_, default=default, min_=min_, max_=max_, var=var):
        return None
    if type_ == OptionTypes.button:
        return CheckOption(name=name, type=OptionTypes.button)
    elif type_ == OptionTypes.check:
        if not default in _check_values:
            return None
        return ButtonOption(name=name, type=OptionTypes.check, default=default)
    elif type_ == OptionTypes.combo:
        if not isinstance(default, str):
            return None
        for v in var:
            if not isinstance(v, str):
                return None
        return ComboOption(
            name=name, type=OptionTypes.combo, default=default, var=tuple(var))
    elif type_ == OptionTypes.spin:
        for a in default, min_, max_:
            if not a.isdigit():
                return None
        return SpinOption(
            name=name,
            type=OptionTypes.spin,
            default=default,
            min=min_,
            max=max_)
    elif type_ == OptionTypes.string:
        if not isinstance(default, str):
            return None
        return StringOption(name=name, type=OptionTypes.string, default=default)
    return None


class InfoParameters(object):
    """The names of parameters in the info command.

    Quoted from the UCI specification (downloaded 9 August 2015):

    @@@
    * info
    the engine wants to send information to the GUI. This should be done
    whenever one of the info has changed.
    The engine can send only selected infos or multiple infos with one info
    command,
    e.g. "info currmove e2e4 currmovenumber 1" or
         "info depth 12 nodes 123456 nps 100000".
    Also all infos belonging to the pv should be sent together
    e.g.
    "info depth 2 score cp 214 time 1242 nodes 2124 nps 34928 pv e2e4 e7e5 g1f3"
    I suggest to start sending "currmove", "currmovenumber", "currline" and
    "refutation" only after one second to avoid too much traffic.
    Additional info:
    * depth <x>
        search depth in plies
    * seldepth <x>
        selective search depth in plies,
        if the engine sends seldepth there must also be a "depth" present in the
        same string.
    * time <x>
        the time searched in ms, this should be sent together with the pv.
    * nodes <x>
        x nodes searched, the engine should send this info regularly
    * pv <move1> ... <movei>
        the best line found
    * multipv <num>
        this for the multi pv mode.
        for the best move/pv add "multipv 1" in the string when you send the pv.
        in k-best mode always send all k variants in k strings together.
    ...
    @@@

    'Additional info:' is read as an abbreviation of 'Additional information:',
    not a reference to 'info' in the '* info' heading.

    'currmove', 'currmovenumber', 'depth', 'nodes', 'nps', 'score', 'time',
    'nodes', 'nps', and 'pv', from the examples in the quote are infos.  'cp'
    from the examples identifies one of the values which may be sent as part of
    the 'score' info.

    The quote recommends sending the 'depth', 'score', 'time', 'nodes', and
    'nps', infos in an info command if the command sends the 'pv' info.  In the
    notes on each info, under the 'additional info:' heading, this point is
    made only for the 'time' info.  The note for the 'multipv' info insists the
    'multipv' info is sent in an info containing the 'pv' info when the engine
    is in "multi pv mode" (in other words 'must' like in the description of
    'seldepth', rather than 'should' like in the description of 'time' for
    example).

    The reference to k-best mode in the description of multipv is interpreted
    as insisting that k consecutive info commands are used to send the pv infos
    for the k variants (in other words string is taken to mean command string,
    not a string containing pv and the moves for the pv).

    In short, info commands could look like:

    'info <info name> <info value> \n'

    where each info command sends one info, or

    'info <info name> <info value> ... \n'

    where each info command sends zero or one value for every info.

    The cases where a single info is not allowed are:
        a pv info is included in the info command: a time info must be present
        a seldepth info is included in the info command: a depth info must be
        present

    If any of the 'depth', 'score'. 'nodes', and 'nps', are to be reported in
    multi pv mode, these infos must be sent in the same info command as the pv
    info.

    A multipv info must be sent in the same info command as a pv info in multi
    pv mode.

    If an info command is sent for one of the k variants in multi pv mode, an
    info command must be sent for all of the k variants and these info commands
    must be consecutive relative to other info commands.  A readyok command in
    response to an isready command is assumed to take precedence over keeping
    the info commands adjacent.

    """
    depth = 'depth'
    seldepth = 'seldepth'
    time = 'time'
    nodes = 'nodes'
    pv = 'pv'
    multipv = 'multipv'
    score = 'score'
    currmove = 'currmove'
    currmovenumber = 'currmovenumber'
    hashfull = 'hashfull'
    nps = 'nps'
    tbhits = 'tbhits'
    sbhits = 'sbhits'
    cpuload = 'cpuload'
    string = 'string'
    refutation = 'refutation'
    currline = 'currline'

    all_ = frozenset((depth,
                      seldepth,
                      time,
                      nodes,
                      pv,
                      multipv,
                      score,
                      currmove,
                      currmovenumber,
                      hashfull,
                      nps,
                      tbhits,
                      sbhits,
                      cpuload,
                      string,
                      refutation,
                      currline,
                      ))
    moves = frozenset((pv, refutation))

    # Regular expression to parse info command
    # re = '(?<= )(depth|seldepth|time| ,,, |string|refutation|currline)\s+'
    ipre = re.compile('|'.join(all_).join(('(?<= )(', ')\s+')))

    @staticmethod
    def parse_info(text):
        """Recturn dict of info parameters extracted from text."""
        ip = InfoParameters
        ipsplit = [t.strip() for t in ip.ipre.split(text)]

        # '<junk> info <parameter name> ... is fine but
        # '<junk> info <junk> <parameter name> ... is not.
        if ipsplit[0].split()[-1] != CommandsFromEngine.info:
            return {}

        # The 'string' info escapes the rest of the line.
        if ip.string in ipsplit:
            i = ipsplit.index(ip.string)
            ipsplit[i+1:] = [' '.join(ipsplit[i+1:])]

        # Verify info command is not ambiguous only.
        for i in ip.all_:
            if ipsplit.count(i) > 1:
                return {}

        o = {}
        for p, v in [ipsplit[i:i+2] for i in range(1, len(ipsplit), 2)]:
            if p in ip.moves:
                o.setdefault(p, []).append(v)
            elif p == ip.currline:
                o[p] = current_line(v)
            elif p == ip.score:
                o[p] = ScoreInfoValueNames.parse_score_info(
                    ' '.join((ip.score, v)))
            else:
                o[p] = v
        return o


class ScoreInfoValueNames(object):
    """The names of score info values and type of value if any."""
    cp = 'cp'
    mate = 'mate'
    lowerbound = 'lowerbound'
    upperbound = 'upperbound'

    all_ = frozenset((cp, mate, lowerbound, upperbound))
    values = frozenset((cp, mate))
    flags = frozenset((lowerbound, upperbound))

    # Regular expression to parse score info value
    # re = '(?<= )(cp|mate|lowerbound|upperbound)\s+'
    sivnre = re.compile('|'.join(all_).join(('(?<= )(', ')\s+')))

    @staticmethod
    def parse_score_info(text):
        """Recturn dict of score info values extracted from text."""
        sivn = ScoreInfoValueNames
        sivnsplit = [t.strip() for t in sivn.sivnre.split(text)]
        o = {}

        # Extract lower and upper bound flags and verify not duplicated.
        # 'cp lowerbound' and so forth are not allowed.
        # Apply sivnre to text with flags removed.
        if sivn.flags.intersection(sivnsplit):
            words = text.split()
            for f in sivn.flags:
                if f in words:
                    if words.count(f) > 1:
                        return {}
                    i = words.index(f)
                    if words[i-1] in sivn.values:
                        return {}
                    if i != len(words) - 1:
                        if words[i+1] not in sivn.all_:
                            return {}
            for f in sivn.flags:
                words.remove(f)
            sivnsplit = [t.strip() for t in sivn.sivnre.split(' '.join(words))]

        # 'score cp <n> mate <m>' without <junk> is fine.
        if sivnsplit[0] != InfoParameters.score:
            return {}

        # Verify score info, cp and mate, is not ambiguous only.
        for s in sivn.values:
            if sivnsplit.count(s) > 1:
                return {}

        for p, v in [sivnsplit[i:i+2] for i in range(1, len(sivnsplit), 2)]:
            if p in sivn.values:
                o[p] = v
            else:
                return {}
        return o


def current_line(text):
    """Return a ( <cpu number>, ( <move1>, ... ) ) tuple from text.

    If the first word of text is digits it is the CPU number.  Otherwise set
    the CPU number to None.

    """
    t = text.split(maxsplit=1)
    if t[0].isdigit():
        return t[0], ' '.join(t[1:])
    else:
        return None, text


InfoSnapshot = namedtuple('InfoSnapshot',
                          (InfoParameters.depth,
                           InfoParameters.seldepth,
                           InfoParameters.time,
                           InfoParameters.nodes,
                           InfoParameters.pv,
                           InfoParameters.multipv,
                           InfoParameters.score,
                           InfoParameters.currmove,
                           InfoParameters.currmovenumber,
                           InfoParameters.hashfull,
                           InfoParameters.nps,
                           InfoParameters.tbhits,
                           InfoParameters.sbhits,
                           InfoParameters.cpuload,
                           InfoParameters.string,
                           InfoParameters.refutation,
                           InfoParameters.currline,
                           'pv_group',
                           ))


class BestmoveParameters(object):
    """The names of parameters in the bestmove command."""
    ponder = 'ponder'

    all_ = frozenset((ponder,))

    # Regular expression to parse option command
    # re = '(?<= )(ponder)\s+'
    bpre = re.compile('|'.join(all_).join(('(?<= )(', ')\s+')))

    @staticmethod
    def parse_bestmove(text):
        """Recturn dict of bestmove values extracted from text."""
        bp = BestmoveParameters
        bpsplit = [t.strip() for t in bp.bpre.split(text)]

        # '<junk> bestmove <move>' or
        # '<junk> bestmove <move> ponder <move>' or
        # 'bestmove <move>' or
        # 'bestmove <move> ponder <move>' or
        # are fine but <junk> any where after 'bestmove' is not.
        
        bm = bpsplit[0].split()
        if len(bm) != 2:
            return {}
        if bm[0] != CommandsFromEngine.bestmove:
            return {}
        o = dict((bm,))

        # Verify bestmove is not ambiguous only.
        for s in bp.all_:
            if bpsplit.count(s) > 1:
                return {}

        for p, v in [bpsplit[i:i+2] for i in range(1, len(bpsplit), 2)]:
            o[p] = v
        return o


class Engine(object):
    """The chess engine state according to commands from engine.

    Info commands from a chess engine are kept in the info attribute: a deque
    of (<info command text>, <InfoSnapshot instance created from text>) tuples
    with each tuple added by the append() method.

    InfoSnapshot is a namedtuple with attributes for every "additional info",
    plus the pv_group attribute to collate the pv "additional info"s received
    between consecutive bestmove commands from a chess engine.

    The pv_group attribute binds to a dictionary shared by all InfoSnapshots
    created between consecutive bestmove commands from a chess engine.

    """
    _empty_infosnapshot = InfoSnapshot(*[None]*(len(InfoParameters.all_) + 1))

    def __init__(self):
        """Create a database state instance."""
        self.name = None
        self.author = None
        self.options = {}
        self.initialize_info_snapshot()

        # Attributes _uciok_expected | _readyok_expected are bound to:
        # None  - at initialisation, when uci | isready has never been sent.
        # False - when uciok | readyok received.
        # True  - when uci | isready sent.
        # A process or thread either looks for uciok | readyok from engines or
        # sends uci | isready to engines, but not both, and some process or
        # thread doing neither makes decisions using these attributes.
        self._uciok_expected = None
        self._readyok_expected = None

        # Attributes copyprotection | registration are bound to:
        # None       - no copyprotection | registration ever received.
        # 'ok'       - copyprotection | registration ok received.
        # 'error'    - copyprotection | registration error received.
        # 'checking' - copyprotection | registration checking received.
        # False      - registration sent after registration error received and
        #              registration checking not yet received.
        #              (copyprotection is never bound to False.)
        self.copyprotection = None
        self.registration = None

    def note_engine_bestmove(self, text):
        """Set self.bestmove to (text, <bestmove extracted from text>).

        If a bestmove was found in text, it should be safe to prune the stack
        of InfoSnapshot objects keeping the only last one.

        However this is left to users of this class because it is not clear
        this interpretation is required of all chess engines.

        A statement equivalent to "del self.info[:-1]" is probably correct if
        the history prior to most recent bestmove is not of interest and the
        pruning is done before the next 'go' command.

        """
        bp = BestmoveParameters
        bestmove = bp.parse_bestmove(text)
        if bestmove:
            self.bestmove = (text, bestmove)

    def note_engine_id(self, text):
        """"""
        ip = IdParameters
        id_ = ip.parse_id(text)
        for k, v in id_.items():
            if k in ip.all_:
                if hasattr(self, k):
                    setattr(self, k, v)

    def note_engine_info(self, text):
        """"""
        ip = InfoParameters
        info = ip.parse_info(text)
        if info:
            if ip.pv in info:

                # Not simply:
                #pv_group = self.snapshot.pv_group
                #pv_group[info.get(ip.multipv)] = info
                #self.snapshot = self.snapshot._replace(**info)
                # because the UCI specification says 'should' not 'must' about
                # grouping and order of infos.  Retain the depth history of
                # each line in case there is doubt which could be resolved.
                pv_group = self.snapshot.pv_group
                if pv_group is None:
                    pv_group = dict()
                depth = info.get(ip.depth)
                if depth is not None:
                    if depth != self.snapshot.depth:
                        if pv_group is self.snapshot.pv_group:
                            pv_group = deepcopy(self.snapshot.pv_group)
                pv_group[info.get(ip.multipv)] = info
                self.snapshot = self.snapshot._replace(
                    pv_group=pv_group, **info)

            else:
                self.snapshot = self.snapshot._replace(**info)
            self.info.append((text, self.snapshot))

    def note_engine_option(self, text):
        """"""
        op = OptionParameters
        option = op.parse_option(text)
        if option:
            self.options[option[op.name]] = (text, option)

    def note_engine_command(self, text):
        """"""
        cfe = CommandsFromEngine
        command = cfe.parse_command(text)
        if command == cfe.info:
            self.note_engine_info(text)
        elif command == cfe.bestmove:
            self.note_engine_bestmove(text)
        elif command == cfe.option:
            self.note_engine_option(text)
        elif command == cfe.id_:
            self.note_engine_id(text)

    def process_engine_response(self, response):
        """"""
        for command_to_engine, result_code, engine_commands in response:
            if result_code:
                self.process_engine_commands(engine_commands)

    def process_engine_commands(self, commands):
        """"""
        n, c = commands
        for i in c:
            self.note_engine_command(i)

    def initialize_info_snapshot(self):
        """Initialize data structures holding commands from chess engines."""
        self.info = deque()
        self.clear_snapshot()

    def clear_snapshot(self):
        """"""
        self.snapshot = self._empty_infosnapshot._replace(pv_group={})
        self.bestmove = None

    @property
    def readyok_expected(self):
        """"""
        return self._readyok_expected

    @readyok_expected.setter
    def readyok_expected(self, value):
        """"""
        self._readyok_expected = bool(value)

    @property
    def uciok_expected(self):
        """"""
        return self._uciok_expected

    @uciok_expected.setter
    def uciok_expected(self, value):
        """"""
        self._uciok_expected = bool(value)

    def set_copyprotection(self, status):
        """"""
        if status in ('ok', 'checking'):
            self.copyprotection = status
        else:
            self.copyprotection = 'error'

    def set_registration(self, status):
        """"""
        if status in ('ok', 'checking', False):
            self.registration = status
        else:
            self.registration = 'error'


EngineInterface = namedtuple(
    'EngineInterface',
    ['driver', 'program_file_name', 'to_driver_queue', 'parser'],
    )
