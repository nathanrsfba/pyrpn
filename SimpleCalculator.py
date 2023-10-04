#!/usr/bin/env python
import inspect
import math
import Calculator

class SimpleCalculator( Calculator.Calculator ):
    """A simpler calculator, for illustrative purposes"""

    PRECISION=8     # Number of digits of precision supported
    NUMTYPE=float   # Type to store numbers as

    def __init__( self ):
        super().__init__()

    def makeButtons( self, landscape=False ):
        """Create the button objects"""

        def button( *args, **kwargs ):
            """Create a button linked to this calculator"""
            return Calculator.OperationButton( self, *args, **kwargs )

        # Digit buttons
        dig = []
        for i in range(10):
            dig.append( Calculator.OperationButton( self, str( i ), str( i ),
                (lambda x: lambda: self.enterDigit( x ))(i) ))

        # Some basic entry buttons
        zero = dig[0]
        bs = button( u"\u232b", "<BackSpace>", lambda: self.backspace() )
        dec = button( ".", ".", lambda: self.decimal() )
        ent = button( u"\u23ce", "<Return>", lambda: self.enter() )

        # Basic arithmetic operations
        add = button( '+', '+', lambda x, y: x + y )
        sub = button( '-', '-', lambda x, y: y - x,
                '-x', (lambda x: -x), extra='_' )
        mul = button( '*', '*', lambda x, y: x * y )
        div = button( '/', '/', lambda x, y: y / x,
                '1/x', lambda x: 1/x, extra='?' )

        # Miscellaneous
        shift = button( u"\u21E7", None, lambda: self.shift() )
        exch = button( u"x\u21c6y", 'x', lambda: self.exchange(),
                'pop', lambda: self.pop() )

        self.portraitButtons = [
                [ bs, div, mul, sub ],
                [ dig[7], dig[8], dig[9], add ],
                [ dig[4], dig[5], dig[6], shift ],
                [ dig[1], dig[2], dig[3], exch ],
                [ zero, zero, dec, ent ]]

        self.landscapeButtons = self.portraitButtons

def getCalculator():
    """Return the defined Calculator class"""
    return SimpleCalculator

def main():
    print( "This is a module and should be imported by a GUI backend " +
            "such as pyrpn.py" )

if __name__ == "__main__":
    main()


