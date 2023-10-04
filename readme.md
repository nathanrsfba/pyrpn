PyRPN
=====

PyRPN is a Reverse Polish Notation calculator, written in Python.

PyRPN is not based on any physical calculator; rather, it was designed with a layout that makes it easy to use with either a hardware keyboard or a touchscreen. All keys have clearly labelled keyboard shortcuts.

RPN calculators are 'stack-based'. When a number is entered, it is placed at the bottom of the stack, and the previous entries all shift up one space. (An operation known as a 'push'.) When a mathematical operation is performed, the bottom two entries (or the bottom entry, for a function that takes a single argument) are removed ('popped') from the stack, the operation is performed, and the result is pushed onto the stack.

Thus, instead of keying two values, with an operation *in between* (as in typical algebraic notation), the operation is keyed *after* its argument(s). A side effect of this is that there is no need for parentheses to determine the order of operations. Operations are entered in the order they occur.

The stack entries are labelled, from the bottom up: X, Y, Z, and T, as is traditional for RPN calculators that display the full stack.

Here are a few examples, showing the difference between entering a calculation in a traditional calculator, vs an RPN calculator:

```
2+2=4:
Alg: 2 + 2 =
RPN: 2 ENTER 2 +

2*(3+4)=20
Alg: 2 * ( 3 + 4 ) =
RPN: 2 ENTER 3 ENTER 4 + *

(1+2)/(3+4)=.428571.....
Alg: ( 1 + 2 ) / ( 3 + 4 ) =
RPN: 1 ENTER 2 + 3 ENTER 4 + /
```

Usage
-----

To enter numbers, simply type it in. To push multiple numbers onto the stack, press the enter button in between numbers.

A > character appears next to the X element when in entry mode. In entry mode, pressing digits appends them to the entered number. When not in entry mode, pressing a digit begins entering a new number onto the stack.

Pressing the enter key in entry mode exits entry mode, so a new number can be entered into the stack. Pressing enter outside of entry mode pushes an additional copy of X onto the stack.

The backspace button will erase the previously entered digit. If the full entry is erased, the aborted entry will be removed from the stack, and entry mode will end.

The shift button will activate a secondary function on some buttons. The button display will change to show the alternate functions.

If an error occurs, an E will be displayed next to the X register, the operation will be ignored, and the stack will remain unchanged.

When using a physical keyboard, all buttons have a keyboard shortcut. The shortcut button will be underlined, except in places where the shortcut is obvious. Either the numeric keypad or the main keyboard may be used. Pressing and holding the shift key will activate the shifted functions. This will not affect keys that require the shift to enter, such as + or * on the main keyboard, or the ^ key for exponentiation.

If the window is resized between portrait and landscape sizes, the layout will change to accommodate the new size

Functions
---------

* +, -, *, /
  Addition, subtraction, multiplication and division
* -x
  Negate the value in the X register
* 1/x
  Take the reciprocal of the X register
* ^
  Exponentiation: Raises Y to the X power
* Root
  Roots: Takes the Xth root of Y; equivalent to raising Y to the 1/x power.
  Note that this returns an error when trying to take the root of a negative
  number, even when it would have a real mathematical result.
* Sqrt
  Takes the square root of X
* Sqr
  Squares X
* !
  Takes the factorial of X. (Technically: Takes the gamma function of X+1,
  returning a result for all non-negative-integer real numbers)
* ln
  Takes the natural logarithm of X
* log
  Takes the base-10 logarithm of X
* Sin, Cos, Tan
  Takes the sine, cosine, and tangent of X in radians
* Asin, Acos, Atan
  Takes the arcsine, arccosine, and arctangent of X, returning radians
* Rad
  Converts X from degrees to radian
* Deg
  Converts X from radians to degrees
* X<->Y
  Swaps the values of X and Y
* popX
  Pops X off the stack and discards it
* Exp
  Takes e to the power of X
* e
  Pushes e onto the stack
* Pi
  Pushes Pi onto the stack
* x*Pi
  Multiplies X by Pi
* AC
  Clear the stack

Memory
------

The calculator has 4 memory slots, aside from the stack, that can be saved and recalled at will. If the window is big enough, the memory will appear next to the stack.

To save a value to a memory slot, press shift, then click the desired memory slot. To load a value from memory and pop it onto the stack, sipmly click the desired memory slot.

On a physical keyboard, pressing Shift followed by F1 through F4 will save to the matching memory slot, and pressing the function key without shift will load it. This works even if the memory slots are not visible.

Technical Details
-----------------

Currently, the calculator supports precision of 8 decimal points, represented internally by a float. This could theoretically be extended, possibly by using a decimal type, or other extended floating point type, or potentially even rationals. Values on the stack are not rounded to fit the visible precision, so the actual stored value might be more precise than what is visible.

Numbers up to 8 digits wide are supported; a calculation that results in a larger number results in an error.

Even though the display only shows four stack entries, the stack is larger than that. The only limit is the amount of memory available to Python.

Math functions are mainly provided by Python's math module, and feature all if its behaviors and limitations.

The code is split into two parts: 

* The 'frontend' GUI code in one file, which is the 'application'
* The 'backend' code, which is a module that defines the behavior of the calculator. This includes the buttons, what they do, and also the calculator's internal state at any given time.

This way, an alternate frontend could be created, such as a PyGTK-based GUI, or even a console-based UI.

The default GUI implementation can load a custom Calculator object. To do so, create a Python file, define a class derived from Calculator, and define a function getCalculator() that returns your new class. To use it, call pyrpn.py with the name of your module. See SimpleCalculator.py for an example.


