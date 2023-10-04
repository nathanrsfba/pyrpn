#!/usr/bin/env python3
import sys
import os.path

import tkinter as tk
import tkinter.font as tkFont
import importlib.machinery
import importlib.util
import configparser

import Calculator

root=tk.Tk()

class Application( tk.Frame ):
    """Frontend for all GUI elements"""

    STACK=4  # Visible stack space
    MEMORY=4 # Visible memory entries

    # Format types
    PORTRAIT=0
    LANDSCAPE=1
    PORTRAITMEM=2
    LANDSCAPEMEM=3

    def __init__( self, calc, master=None):
        tk.Frame.__init__( self, master, relief='sunken' )

        self.config = self.getConfig()
        self.master.title( 'PyRPN' )
        self.shifted = False
        self.shiftLock = False
        self.layout = None
        self.buttons = None

        top = self.winfo_toplevel()
        top.rowconfigure( 0, weight=1 )
        top.columnconfigure( 0, weight=1 )
        top.wm_geometry( self.config['general']['geometry'] )
        self.grid( sticky=tk.N+tk.E+tk.S+tk.W )
        self.columnconfigure( 0, weight=1 )
        self.rowconfigure( 1, weight=1 )

        self.createFonts()
        self.createWidgets()
        self.createBindings()
        self.initCalc( calc )
        self.createButtons()
        self.format()

        root.protocol( 'WM_DELETE_WINDOW', self.onClose )

        iconpath = os.path.join(
            os.path.dirname( os.path.realpath( __file__ )),
            'icon.png' )
        root.iconphoto( True, tk.PhotoImage( file=iconpath ))


    def createFonts( self ):
        """Create fonts used by the app"""

        family = tk.font.nametofont( 'TkFixedFont' ).actual()['family']
        size=self.config.getint( 'general', 'numbersize' )
        self.digitFont = tkFont.Font( family=family, size=size, weight='bold' )
        family = tk.font.nametofont( 'TkDefaultFont' ).actual()['family']
        size=self.config.getint( 'general', 'buttonsize' )
        self.buttonFont = tkFont.Font( family=family, size=size )

    def createWidgets( self ):
        """Create all the widgets for the app, except buttons"""

        # Create the stack display
        self.stackframe = sf = tk.Frame( self, 
                borderwidth=2, relief='groove' )
        self.stack = []
        labels = ('X', 'Y', 'Z', 'T')
        for r in range(self.STACK):
            label = tk.Label( sf, text=labels[self.STACK - r - 1] )
            label.grid( column=0, row=r )
            
            disp = CalcDisplay( sf, font=self.digitFont )
            self.stack.append( disp )
            disp.grid( column=1, row=r )
            disp.setValue( 0 )

        # Create the memory display
        self.memoryframe = mf = tk.Frame( self )
        self.memory = []
        for r in range(self.MEMORY):
            label = tk.Label( mf, text=f" {r + 1} ", 
                    relief='groove')
            label.grid( column=0, row=r, sticky=tk.N+tk.E+tk.S+tk.W ) 
            label.bind( "<Button-1>",
                    lambda e,r=r: self.clickMemory( r + 1 ))
            
            disp = CalcDisplay( mf, font=self.digitFont )
            disp.configure( relief='groove' )
            self.memory.append( disp )
            disp.grid( column=1, row=r, sticky=tk.N+tk.E+tk.S+tk.W ) 
            disp.setValue( 0 )
            disp.bind( "<Button-1>",
                    lambda e,r=r: self.clickMemory( r + 1 ))
            mf.columnconfigure( 0, weight=1 )

        # Error indicator
        self.err = tk.StringVar()
        err = tk.Label( sf, text='', font=self.digitFont,
                textvariable=self.err )
        err.grid( column=2, row=self.STACK - 1 )
        self.err.set( ' ' )

        # Create the button frame, although it won't be populated until
        # we initialize the Calculator
        self.buttonframe = bf = tk.Frame( self, relief='sunken' )
        bf.grid( row=1, sticky=tk.N+tk.E+tk.S+tk.W )


    def bindkey( self, key, action ):
        """Bind a key to an action"""
        self.master.bind( key, action )
        # If the key is a lowercase letter, bind the uppercase
        # version as well
        if len( key ) == 1 and key != key.upper():
            self.master.bind( key.upper(), action )

        # Try binding keypad codes separately, as some implementations
        # (X Windows) require it
        try:
            if "1234567890".find( key ) >= 0:
                self.master.bind( f"<KP_{key}>", action )
            # Translate regular keys to keypad equivalents
            translates = {
                    '<Return>': '<KP_Enter>',
                    '+': '<KP_Add>',
                    '-': '<KP_Subtract>',
                    '*': '<KP_Multiply>',
                    '/': '<KP_Divide>',
                    '.': '<KP_Decimal>',
                    '=': '<KP_Equal>'
                    }
            if key in translates:
                self.master.bind( translates[key], action )
        except tk._tkinter.TclError:
            # Keysym doesn't exist, probably not needed on this
            # system
            pass



    def createBindings( self ):
        """Create the various global event bindings"""
        self.bindkey( "<KeyPress-Shift_L>", self.shift )
        self.bindkey( "<KeyRelease-Shift_L>", self.unshift )
        self.bindkey( "<KeyPress-Shift_R>", self.shift )
        self.bindkey( "<KeyRelease-Shift_R>", self.unshift )
        self.bindkey( "<Escape>", lambda _: self.calc.clearStack() )
        self.winfo_toplevel().bind( "<Configure>", self.onResize )
        for i in range( self.MEMORY ):
            self.bindkey( f"<Shift-F{i+1}>", 
                    lambda e, i=i: self.calc.saveMemory( i + 1 ))
            self.bindkey( f"<F{i+1}>", 
                    lambda e, i=i: self.calc.loadMemory( i + 1 ))
        self.bindkey( "<F5>", lambda _: self.configDialog() )


    def initCalc( self, calc ):
        """Initialise all data connected to calculator backend"""
        # Link us to the calculator, and vice-versa
        self.calc = calc
        calc.gui = self

    def createButtons( self ):
        """Create the button widgets"""
        # The button layout, from calc
        buttons = self.calc.getButtons()
        # The TK button objects, in a 2d list
        widgets = []
        # Running count of rows
        rows = 0
        for row in buttons:
            # The widgets in this row
            rowwidgets = []
            widgets.append( rowwidgets )
            rows += 1
            # Running count of columns
            cols = 0
            for b in row:
                cols += 1
                if b and rows > 1 and b is buttons[rows-2][cols-1]:
                    # If the same button exists directly above us,
                    # take no further action
                    pass
                elif b and cols > 1 and b is buttons[rows-1][cols-2]:
                    # ...same if it exists directly left of us
                    pass
                elif b:
                    # Create the button, but don't actually place it yet
                    button = CalcButton( self.buttonframe, b,
                            relief='groove', font=self.buttonFont ) 
                    button.configure(
                            command=lambda b=b: self.press( b ))
                    b.data = button
                    rowwidgets.append( button )
                    if b.key:
                        self.bindkey( b.key, lambda _, b=b: self.press( b ))
                    if b.extra:
                        self.bindkey( b.extra, lambda _, b=b: self.press( b ))

        self.buttons = widgets

    def arrangeButtons( self ):
        """Position the buttons in their parent object"""
        if not self.buttons: return
        buttons = self.calc.getButtons()
        if( not self.isPortrait() ):
            buttons = self.calc.getButtons( True )
        # The TK button objects
        widgets = []
        # Running count of rows
        rows = 0
        for row in buttons:
            # The widgets in this row
            rowwidgets = []
            widgets.append( rowwidgets )
            rows += 1
            # Running count of columns
            cols = 0
            for b in row:
                cols += 1
                # If the button already exists either above us or to the 
                # left, then it's a double-size button, and we should
                # modify the already defined one to span two cells
                if b and rows > 1 and b is buttons[rows-2][cols-1]:
                    widgets[rows-2][cols-1].grid( rowspan=2 )
                elif b and cols > 1 and b is buttons[rows-1][cols-2]:
                    widgets[rows-1][cols-2].grid( columnspan=2 )
                # Otherwise, grid it
                elif b:
                    button = b.data
                    button.grid( column=cols-1, row=rows-1, 
                            sticky=tk.N+tk.E+tk.S+tk.W )
                    rowwidgets.append( button )

        for row in range(rows):
            self.buttonframe.rowconfigure( 
                    row, weight=1, uniform='buttons' )
        for col in range(cols):
            self.buttonframe.columnconfigure( 
                    col, weight=1, uniform='buttons' )

        # Resize away unused rows/cols
        (wrows, wcols) = self.buttonframe.grid_size()
        for row in range(rows, wrows):
            self.buttonframe.rowconfigure( row, weight=0, uniform='' )
        for col in range(cols, wcols):
            self.buttonframe.columnconfigure( col, weight=0, uniform='' )

        self.buttons = widgets

    def entry( self, entry ):
        """Place the entered number into the bottom stack element"""
        self.stack[-1].entry( entry )

    def drawStack( self ):
        """Update the stack display with contents of calculator"""

        for x in range(self.STACK):
            self.stack[-1-x].setValue( self.calc.getRegister( x ))

        for x in range(self.MEMORY):
            self.memory[x].setValue( self.calc.getMemory( x + 1 ))

    def press( self, button ):
        """Fire the action (or alt action) for the given button"""

        self.error( False )
        oldshift = self.shifted

        if self.shifted and button.alt:
            button.alternate()
        else:
            button.action()

        # Unshift ourselves, unless the button changed our shifted state
        if self.shiftLock and self.shifted == oldshift:
            self.unshift()

    def shift( self, _=None ):
        """Turn on shift"""
        if( self.shifted ): return
        self.doShift( True )

    def unshift( self, _=None ):
        """Turn off shift"""
        self.doShift( False )

    def updateButtons( self ):
        """Update all button labels"""
        shifted = self.shifted
        for r in self.buttons:
            for b in r:
                b.setLabel( shifted )

    def doShift( self, shifted ):
        """Set shifted state"""
        self.shifted = shifted
        self.updateButtons()
        if not shifted:
            self.shiftLock = False

    def toggleShift( self ):
        """Toggle locked shift stae"""
        if self.shifted:
            self.unshift()
        else:
            self.shift()
            self.shiftLock = True

    def clickMemory( self, pos ):
        """Save memory at position if shifted, else load it"""

        # print( self.shifted )
        if self.shifted:
            self.calc.saveMemory( pos )
        else:
            self.calc.loadMemory( pos )

        self.unshift()


    def error( self, error=True ):
        """Set or clear the error indicator"""

        if error:
            self.err.set( 'E' )
        else:
            self.err.set( ' ' )

    def onResize( self, event ):
        """Catch resize events, and reformat ourselves if necessasry"""
        # Filter out anything except toplevel changes
        if event.widget != self.winfo_toplevel(): return

        self.format()

    def format( self, layout=None, force=False ):
        """Arrange widgets appropriately to the window shape"""
        sh = self.stackframe.winfo_reqheight()
        if sh == 1: return # Windows hasn't been displayed yet
        sw = self.stackframe.winfo_reqwidth()
        if not layout:
            top = self.winfo_toplevel()
            height = top.winfo_height()
            width = top.winfo_width()
            if width >= height:
                layout=self.LANDSCAPE
                if height > 2*sh:
                    layout=self.LANDSCAPEMEM
            else:
                layout=self.PORTRAIT
                if width > 2*sw:
                    layout=self.PORTRAITMEM

        if self.layout == layout and not force:
            return

        self.layout = layout
        self.arrangeButtons()

        if( self.isPortrait() ):
            self.stackframe.grid( row=0, column=1 )
            self.buttonframe.grid( row=1, column=0, rowspan=1, columnspan=2 )
            self.rowconfigure( 0, weight=0 )
            self.rowconfigure( 1, weight=1 )
            self.columnconfigure( 0, weight=0 )
            self.columnconfigure( 1, weight=1 )
            self.stackframe.grid( sticky=tk.N+tk.S+tk.E )
            if self.memoryVisible():
                self.memoryframe.grid( column=0, row=0, 
                        sticky=tk.N+tk.E+tk.S+tk.W ) 
            else:
                self.memoryframe.grid_remove()
        else:
            if self.config.getboolean( 'general', 'displayleft' ):
                dc=0
            else:
                dc=1
            bc=1 - dc
            self.stackframe.grid( row=0, column=dc )
            self.buttonframe.grid( row=0, column=bc, rowspan=2 )
            self.rowconfigure( 0, weight=1 )
            self.rowconfigure( 1, weight=0 )
            self.columnconfigure( dc, weight=0 )
            self.columnconfigure( bc, weight=1 )
            self.stackframe.grid( sticky=tk.N+tk.W+tk.E )
            if self.memoryVisible():
                self.memoryframe.grid( column=dc, row=1, 
                        sticky=tk.N+tk.E+tk.S+tk.W ) 
            else:
                self.memoryframe.grid_remove()


    def isPortrait( self ):
        """Are we in portrait mode?"""
        return self.layout in (self.PORTRAIT, self.PORTRAITMEM)

    def memoryVisible( self ):
        """Are the memory cells visible?"""
        return self.layout in (self.PORTRAITMEM, self.LANDSCAPEMEM)

    def resizeFonts( self ):
        """Reset the font sizes after a configuration change"""

        self.createFonts()
        for w in self.stack + self.memory:
            w.configure( font=self.digitFont )
        for r in self.buttons:
            for w in r:
                w.configure( font=self.buttonFont )



    def getConfigFile( self ):
        """Return that path to the configuration file"""

        return os.path.join( os.path.expanduser( '~' ), '.pyrpn' )

    def getConfig( self ):
        """Read the configuration and return it"""
        
        cf = self.getConfigFile()
        cp = configparser.ConfigParser()

        # Set some defaults
        cp['general'] = {
                'geometry': "250x400",
                'numbersize': 12,
                'buttonsize': 10,
                'displayleft': True
                }

        cp.read( cf )
        return cp

    def writeConfig( self ):
        """Write the configuration"""

        cf = self.getConfigFile()
        cp = self.config

        top = self.winfo_toplevel()
        geometry = top.winfo_geometry()
        self.config['general']['geometry'] = geometry

        with open( cf, 'w' ) as f:
            cp.write( f )

    def configDialog( self ):
        """Display the configuration dialog"""

        dlg = ConfigDialog( self )
        dlg.focus_set()

    def quit( self, *args, **kwargs ):
        """Exit the app"""

        self.writeConfig()
        super().quit( *args, **kwargs )

    def onClose( self ):
        """Exit when the window is closed"""
        self.quit()


class CalcDisplay( tk.Label ):
    """Display a register on the stack"""

    WIDTH=8        # Visible precision

    def __init__( self, parent, *args, **kwargs ):
        self.content = content = tk.StringVar()
        super().__init__( parent, textvariable=content, *args, **kwargs )
        self.setValue( 0 )

    def setValue( self, value ):
        """Store value given and display it"""
        self.content.set( fmtfloat( value, self.WIDTH ))
        
    def entry( self, value ):
        """Display the given string, as entered by user"""
        (whole, sep, decimal) = value.partition( '.' )
        self.content.set(
                f">% {self.WIDTH}s%1s%-{self.WIDTH}s" % 
                (whole, sep, decimal) )

def fmtfloat( value, width ):
    """Format a floating point value to a string

    This will convert a floating point value into a string. The width
    argument specifies the width of both the whole and decimal portions.
    Any extra zeroes and decimal points will be stripped off the end.
    """
    value = round( value, width )
    return ((f"% {width * 2 + 2}.{width}f" % value)
            .rstrip( '0' ) .rstrip( '.' ) .ljust( width * 2 + 2 ))

class CalcButton( tk.Button ):
    """Calculator button

    This is mostly just a button widget, but keeps track of the
    backend button object and uses it to set its own label
    """
    def __init__( self, parent, button, *args, **kwargs ):
        super().__init__( parent, *args, **kwargs, 
                text=button.getLabel() )
        self.button = button
        self.setLabel()

    def setLabel( self, shifted=False ):
        """Update the label"""
        b = self.button
        if b.key:
            name = b.getLabel( shifted )
            self.configure( text=name )
            if( b.key in name.lower() and name != b.key ):
                self.configure( underline=name.lower().index( b.key ))
            else:
                self.configure( underline=-1 )

class ConfigDialog( tk.Toplevel ):
    def __init__( self, app, *args, **kwargs ):
        super().__init__( app, *args, **kwargs )
        self.geometry( f"+{root.winfo_x() + 100}+{root.winfo_y() + 100}" )
        self.app = app
        self.transient( app )
        self.title( 'Configuration' )

        self.displayleft = var = tk.IntVar()
        cb = tk.Checkbutton( self, 
                text="Display on left in landscape mode",
                variable=var )
        if app.config.getboolean( 'general', 'displayleft' ):
            cb.select()
        cb.grid( row=0, column=0, columnspan=2, sticky=tk.W )

        label = tk.Label( self, text="Display font size" )
        label.grid( row=1, column=0, sticky=tk.W  )
        self.dispfont = var = tk.IntVar()
        var.set( app.config.getint( 'general', 'numbersize' ))
        spin = tk.Spinbox( self, 
                from_=1, to=99, increment=1, textvariable=var )
        spin.grid( row=1, column=1 )

        label = tk.Label( self, text="Button font size" )
        label.grid( row=2, column=0, sticky=tk.W  )
        self.butfont = var = tk.IntVar()
        var.set( app.config.getint( 'general', 'buttonsize' ))
        spin = tk.Spinbox( self, 
            from_=1, to=99, increment=1, textvariable=var )
        spin.grid( row=2, column=1 )

        frame = tk.Frame( self )
        frame.grid( row=3, column=0, columnspan=2 )
        button = tk.Button( frame, text='OK', command=self.save )
        button.grid( row=3, column=0 )
        button = tk.Button( frame, text='Cancel', command=self.destroy )
        button.grid( row=3, column=1 )

        self.bind( '<Escape>', lambda _: self.destroy() )
        self.bind( '<Return>', lambda _: self.save() )

    def save( self ):
        section = self.app.config['general']
        section['displayleft'] = str( self.displayleft.get() )
        section['numbersize'] = str( self.dispfont.get() )
        section['buttonsize'] = str( self.butfont.get() )
        self.app.format( force=True )
        self.app.resizeFonts()
        self.destroy()

def main():
    calcMod = Calculator
    if( len( sys.argv ) > 1 ):
        module = sys.argv[1]
        calcMod = importlib.import_module( module )


    calc = calcMod.getCalculator()()
    app = Application( calc )
    app.mainloop()


if __name__ == "__main__":
    main()


