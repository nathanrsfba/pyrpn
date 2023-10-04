#!/usr/bin/env python
import inspect
import math

class ButtonBase:
    """A button that performs a calculator operation"""
    def __init__( self, calc, name, key, alt=None, extra=None ):
        """Initialize the button

        Arguments:
        calc -- Reference to the calculator object parent
        name -- The name of the button, to be shown on the label. This
                should be in Tk event binding format. This may be a single
                visible ASCII character, or a special key in angle
                brackets, such as <Return>
        key -- The keyboard shortcut
        alt -- The name of the alternate function, if it has one
        extra -- An extra key that will also be bound to this button
        """

        self.name = name
        self.key = key
        self.alt = alt
        self.extra = extra
        self.calc = calc

        # A slot for the frontend to store data in
        self.data = None

    def action( self ):
        """Perform the primary operation"""
        pass

    def alternate( self ):
        """Perform the shifted operation, if defined"""
        pass

    def getLabel( self, shifted=False ):
        if shifted and self.alt:
            return self.alt
        else:
            return self.name

class OperationButton( ButtonBase ):
    """A button that performs an operation on the stack"""
    def __init__( self, calc, name, key, lam, 
            alt=None, altlam=None, **kwargs ):
        """Initialize the button

        Arguments:
        calc -- Reference to the calculator object parent
        name -- The name of the button, to be shown on the label
        key -- The keyboard shortcut
        lam -- A lambda (or other callable) that may take up to two arguments,
               which is called when the button is pressed.
               If zero arguments: The function is called without
               further fanfare.
               If one or two arguments: Any current entry will be finalized.
               The one/two values will be popped off the stack, passed to the
               function, and the return pushed back onto the stack, updating
               the display.  If an ArithmeticError or ValueError occurs, or if
               the result exceeds the calculator's defined precision, set the
               error indicator, and ignore the operation
        alt -- The name of the alternate function, if it has one
        altlam -- The lambda for the alternate function, in the same form
                  as above
        **kwargs -- Additional keyword arguments to pass to ButtonBase
                    constructor
        """

        super().__init__( calc, name, key, alt, **kwargs )
        self.calc = calc
        self.lam = lam
        self.altlam = altlam

    def action( self ):
        self.do( self.lam )

    def alternate( self ):
        if( self.altlam ):
            self.do( self.altlam )

    def do( self, lam ):
        """Call the stored lambda"""

        args = len( inspect.signature( lam ).parameters )
        if args == 0: 
            lam()
        elif args == 1:
            calc = self.calc
            calc.finalizeEntry()
            x = calc.pop( True )
            try:
                value = lam( x )
                if( value >= 10 ** calc.PRECISION ):
                    raise ArithmeticError
                calc.push( value )
            except (ValueError, ArithmeticError):
                calc.push( x )
                calc.gui.error()
        elif args == 2:
            calc = self.calc
            calc.finalizeEntry()
            x = calc.pop( True )
            y = calc.pop( True )
            try:
                value = lam( x, y )
                if( value >= 10 ** calc.PRECISION ):
                    raise ArithmeticError
                calc.push( value )
            except (ValueError, ArithmeticError):
                calc.push( y, True )
                calc.push( x )
                calc.gui.error()

class TrigButton( ButtonBase ):
    """A trig button that accounts for angle mode and hyperbolic mods"""

    def __init__( self, calc, key,
            tname, tfunc, itname, itfunc,
            hname, hfunc, ihname, ihfunc ):
        super().__init__( calc, 'XXX', key, 'XXX' )
        self.tname = tname
        self.tfunc = tfunc
        self.itname = itname
        self.itfunc = itfunc
        self.hname = hname
        self.hfunc = hfunc
        self.ihname = ihname
        self.ihfunc = ihfunc

    def getLabel( self, shifted=False ):
        if not shifted:
            if self.calc.hyper:
                return self.hname
            else:
                return self.tname
        else:
            if self.calc.hyper:
                return self.ihname
            else:
                return self.itname

    def action( self ):
        x = self.calc.pop()
        a = x
        if self.calc.angles == Calculator.DEG:
            a = math.radians( a )

        try:
            if self.calc.hyper:
                value = self.hfunc( a )
            else:
                value = self.tfunc( a )
            self.calc.push( value )
        except (ValueError, ArithmeticError):
            self.calc.push( x )
            self.calc.gui.error()

    def alternate( self ):
        x = self.calc.pop()

        try:
            if self.calc.hyper:
                value = self.ihfunc( x )
            else:
                value = self.itfunc( x )
            if self.calc.angles == Calculator.DEG:
                value = math.degrees( value )
            self.calc.push( value )
        except (ValueError, ArithmeticError):
            self.calc.push( x )
            self.calc.gui.error()

class TrigModeButton( ButtonBase ):
    """A button to switch trig function modes"""

    def __init__( self, calc ):
        super().__init__( calc, 'Deg', 'd', 'Hyp', 'h')

    def getLabel( self, shifted=False ):
        if not shifted:
            if self.calc.angles == Calculator.DEG:
                return 'Deg'
            else:
                return 'Rad'
        else:
            return self.alt

    def action( self ):
        if self.calc.angles == Calculator.DEG:
            self.calc.angles = Calculator.RAD
        else:
            self.calc.angles = Calculator.DEG
        self.calc.gui.updateButtons()

    def alternate( self ):
        self.calc.hyper = not self.calc.hyper
        self.calc.gui.updateButtons()

class Calculator:
    """Backend for all calculator operations"""

    PRECISION=8     # Number of digits of precision supported
    NUMTYPE=float   # Type to store numbers as

    RAD=0
    DEG=1
    GRAD=2

    def __init__( self ):
        self.entry = None #  Currently entering number
        self.stack = []
        self.memory = []
        self.gui = None
        self.angles = self.RAD
        self.hyper = False # In hyperbolic function mode?

        self.makeButtons()

    def push( self, value, silent=False ):
        """Push a value onto the stack"""

        self.finalizeEntry()
        self.stack.append( value )
        if( not silent ): self.gui.drawStack()

    def pop( self, silent=False ):
        """Pop the last value off the stack and return it"""
        self.finalizeEntry()
        value = 0
        if self.stack:
            value = self.stack.pop()

        if( not silent ): self.gui.drawStack()
        return value

    def getRegister( self, pos ):
        """Return the given register off the stack

           pos -- The index of the register to return, with X being location
                  0. If the requested index is beyond the end of the stack,
                  return 0
        """

        if pos < len( self.stack ):
            return self.stack[-1-pos]
        else:
            return 0

    def enterDigit( self, digit ):
        """Enter the pressed digit into the bottom stack entry"""
        if( self.entry == None ):
            self.push( 0 )
            self.entry = ""

        (whole, sep, dec) = self.entry.partition( '.' )

        if( sep == '' ):
            if len( whole ) >= self.PRECISION: return
        else:
            if len( dec ) >= self.PRECISION: return

        if self.entry == '0':
            self.entry = str( digit )
        else:
            self.entry += str( digit )
        self.gui.entry( self.entry )

    def finalizeEntry( self ):
        """Update the stack with the entered number and redraw"""

        if not self.entry: return
        if not self.stack:
            self.stack.append( 0 )
        self.stack[-1] = self.NUMTYPE( '0' + self.entry )
        self.entry = None
        self.gui.drawStack()

    def enter( self ):
        """Finalize if in entry mode, otherwise duplicate X"""

        if self.entry:
            self.finalizeEntry()
        else:
            if self.stack:
                self.push( self.stack[-1] )
            else:
                self.push( 0 )

    def shift( self ):
        """Toggle shifted state"""

        self.gui.toggleShift()

    def decimal( self ):
        """Insert decimal point, if not already present"""

        if not self.entry: 
            self.push( 0 )
            self.entry='0.'
        elif '.' in self.entry: 
            return
        else:
            self.entry += '.'
        self.gui.entry( self.entry )

    def backspace( self ):
        """Backspace out the last entered digit"""
        if( not self.entry ): return

        self.entry = self.entry[0:-1]
        if self.entry == '' or self.entry == '0':
            self.entry = None
            self.pop()
        else:
            self.gui.entry( self.entry )

    def exchange( self ):
        """Exchange x and y"""

        self.finalizeEntry()
        x = self.pop( True )
        y = self.pop( True )
        self.push( x, True )
        self.push( y )

    def clearStack( self ):
        """Clear the stack"""
        self.stack = []
        self.entry = None
        self.gui.drawStack()

    def saveMemory( self, pos ):
        """Save X to the given memory location"""

        self.finalizeEntry()
        if len( self.memory ) < pos:
            self.memory.extend( [0] * (pos - len( self.memory )) )
        self.memory[pos - 1] = self.getRegister( 0 )
        self.gui.drawStack()

    def loadMemory( self, pos ):
        """Push given memory location onto the stack

           pos -- The memory location to return, which is 1-based
        """

        self.push( self.getMemory( pos ))

    def getMemory( self, pos ):
        """Get value of given memory location"""

        if len( self.memory ) >= pos:
            return self.memory[pos - 1]

        return 0

    def getButtons( self, landscape=False ):
        """Retrieve the layout of buttons for this calculator

        This will return a two-dimensional array of ButtonBase objects,
        corresponding to the desired layout of the calculator. The same
        button may appear twice, side-by-side or above-and-below: This
        represents a single double-sized button.
        """
        if landscape:
            return self.landscapeButtons
        return self.portraitButtons

    def makeButtons( self, landscape=False ):
        """Create the button objects"""

        def button( *args, **kwargs ):
            """Create a button linked to this calculator"""
            return OperationButton( self, *args, **kwargs )

        # Digit buttons
        dig = []
        for i in range(10):
            dig.append( OperationButton( self, str( i ), str( i ),
                (lambda x: lambda: self.enterDigit( x ))(i) ))

        # Some basic entry buttons
        zero = dig[0]
        bs = button( u"\u232b", "<BackSpace>", self.backspace,
                'AC', self.clearStack )
        dec = button( ".", ".", self.decimal )
        ent = button( u"\u23ce", "<Return>", self.enter )

        # Basic arithmetic operations
        add = button( '+', '+', lambda x, y: x + y )
        sub = button( '-', '-', lambda x, y: y - x,
                '-x', (lambda x: -x), extra='_' )
        mul = button( '*', '*', lambda x, y: x * y )
        div = button( '/', '/', lambda x, y: y / x,
                '1/x', lambda x: 1/x, extra='?' )

        # Trig-related functions
        sin = TrigButton( self, 's',
                'Sin', math.sin,
                'Asin', math.asin,
                'Sinh', math.sinh,
                'Asinh', math.asinh )
        cos = TrigButton( self, 'c',
                'Cos', math.cos,
                'Acos', math.acos,
                'Cosh', math.cosh,
                'Acosh', math.acosh )
        tan = TrigButton( self, 't',
                'Tan', math.tan,
                'Atan', math.atan,
                'Tanh', math.tanh,
                'Atanh', math.atanh )
        deg = TrigModeButton( self )

        # Exponential-related functions
        shift = button( u"\u21E7", None, self.shift )
        pwr = button( '^', '^', lambda x, y: math.pow( y, x ))
        root = button( "Root", 'r', lambda x, y: math.pow( y, 1 / x ),
                '!', lambda x: math.gamma( x + 1 ), extra='!' )
        sqr = button( 'Sqrt', 'q', math.sqrt,
                'Sqr', lambda x: math.pow( x, 2 ))
        ln = button( 'ln', 'l', lambda x: math.log( x ),
                'log', lambda x: math.log10( x ))

        # Miscellaneous
        exch = button( u"x\u21c6y", 'x', self.exchange,
                'popX', self.pop )
        exp = button( 'Exp', 'e', math.exp,
                'e', lambda: self.push( math.e ))
        pi = button( 'Pi', 'p', lambda: self.push( math.pi ),
                'x*Pi', lambda x: x * math.pi )

        self.portraitButtons = [
                [ shift, exch, exp, pi ],
                [ sin, cos, tan, deg ],
                [ pwr, root, sqr, ln ],
                [ bs, div, mul, sub ],
                [ dig[7], dig[8], dig[9], add ],
                [ dig[4], dig[5], dig[6], add ],
                [ dig[1], dig[2], dig[3], ent ],
                [ zero, zero, dec, ent ]]

        self.landscapeButtons = [
                [ exch, sin, pwr, dig[7], dig[8], dig[9], sub, bs ],
                [ exp, cos, root, dig[4], dig[5], dig[6], mul, div ],
                [ pi, tan, sqr, dig[1], dig[2], dig[3], add, ent ],
                [ shift, deg, ln, zero, zero, dec, add, ent]]

def getCalculator():
    """Return the defined Calculator class"""
    return Calculator

def main():
    import pyrpn
    pyrpn.main()

if __name__ == "__main__":
    main()


