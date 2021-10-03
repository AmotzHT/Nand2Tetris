// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(LOOP)
@KBD
D=M
@BLACK
D;JNE
@WHITE
D;JEQ

(BLACK)
@8192
D=A
@i
M=D
(LOOPBLACK)
@SCREEN
D=D+A
A=D
M=-1

@i
D=M-1
M=D
@LOOP
D;JLT

@LOOPBLACK
0;JMP

(WHITE)
@8192
D=A
@i
M=D
(LOOPWHITE)
@SCREEN
D=D+A
A=D
M=0

@i
D=M-1
M=D
@LOOP
D;JLT

@LOOPWHITE
0;JMP

@LOOP
0;JMP