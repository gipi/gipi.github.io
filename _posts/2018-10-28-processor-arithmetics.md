---
layout: post
comments: true
title: "Integer arithmetic from a computer point of view"
tags: [arithmetic, low level, WIP]
---

A thing that is overlooked is the way arithmetic operations work in a computer
and specifically in the processing unit: not having a clear idea of how
the operations are performed and their limitations can cause very important
bug to happen and also help in case you want to reverse unknown code.

First of all, the arithmetic inside a CPU is done on register of fixed
size via the ``ALU`` and since the register are size limited, all the
arithmetic operations are intended modulo the size of the registers.

## Integer encoding

We are interested of the case of a register containing a number: since
the register has a fixed number of bits (let's say is \\(N\\)) we can
only represent (directly) unsigned values between \\(0\\) and \\(2^N - 1\\).

The formula is the following

$$
b = \sum_{i = 0}^{N - 1} b_i 2^i
$$

Remember the following properties for binary numbers: **completness**

$$
\sum_{n = 0}^{N} 2^n = 2^{N + 1} - 1
$$

and **shifting - multiplication relation**

$$
\eqalign{
2\cdot2^N &= 2^N + 2^N \cr
          &= 2^N + \sum_{i = 0}^{N - 1} 2^i + 1 \cr
          &= 2^N + 2^{N - 1} + 2^{N - 2} + \dots + 2^1 + 2^0 + 1 \cr
          &= \sum_{i = 0}^N 2^i + 1 \cr
          &= 2^{N + 1} - 1 + 1 \cr
          &= 2^{N + 1} \cr
}
$$

that means that left shifting a binary number is equivalent to multiplying
the same number for a power of two.

For signed numbers there is not a unique way to represent them: the quick
and dirty way would be to use the most significant bit as **sign bit**;
this has two drawbacks:

 1. when you add a positive and negative number together you have to invert the
operation to be a subtraction (and viceversa) and this need a circuitery in
the processor.
 2. you have two zeros

I think that this encoding is not used by anyone in the real world (but I could be
wrong), there are more efficient ways.

### One's complement

It consists in flipping all the bits of a number, in this way
if you define the negative of a given number as the one's complement
of it you have the nice property that this two numbers summed are equal
to zero and you don't have to implement any particular circuitery
on the processor since the operations are executed as usual.

The problem is that you have two zeros: all bits equal to zero and all
equal to one.

### Two's complement

It's an extension of the one's complement: to obtain the negative representation
of a number you have to take the one's complement and add one: in this way you have
an asymmetry between the minimum and maximum number that can be represented, i.e.
you can represent values between \\(-2^{N - 1}\\) and \\(2^{N - 1} - 1\\). For example
with 7 bits you have the interval \\((-64, 63)\\).

$$
w = - a_{N - 1}\, 2^{N - 1} + \sum_{i = 0}^{N - 2} a_i\,2^i
$$

Normally in the code is this the way the negative numbers are represented.

Remember that a value into a register is not signed or unsigned by itself,
it depends on how is used in the code.

## Operations

### Sign extension

In certain cases could be necessary to do operations between numbers having a different
number of bits; if these numbers are unsigned it's not big deal, but if instead we having
signed ones we have to **sign extend** i.e. to complete the bits of the extended number
with all ``1``s.

Let me make an example: if we have a 8-bit register with the decimal value \\(-16\\),
its representation with two's complement will be ``0xef``; now, if we want to put this
value into a 16-bit register and represent the same number, we have to set as most significant
byte ``0xff``, i.e. ``0xffef``: this because of a nice property of binary numbers, namely

in our case we have the Mth bit used for the sign and suppose we have other \\(s\\) bits

$$
\eqalign{
-2^M + \sum_{i=s}^{M-1} 2^i + \sum_{i=0}^{s - 1} 2^i &= - 1 \cr
-2^M + \sum_{i=s}^{M - 1} 2^i                        &= \sum_{i=0}^{s - 1} 2^i - 1 \cr
-2^M + \sum_{i=s}^{M - 1} 2^i                        &= 2^{s} - 1
}
$$

$$
\eqalign{
\left(-2^N + 2^{N - 1} + 2^{N - 2} + \dots + 2^s\right) - \left(-2^s\right) &= -2^N + 2^{N - 1} + 2^{N - 2} + \dots + 2^s + 2^s \cr
 &= -2^N + 2^{N - 1} + 2^{N - 2} + \dots + 2^s + \left[\left(\sum_{i = 0}^{s - 1}2^i\right) + 1\right] \cr
 &= -2^N + 2^{N - 1} + 2^{N - 2} + \dots + 2^s + 2^{s - 1} + 2^{s - 2} + \dots + 2 + 2^0 + 1 \cr
 &= -2^N + \sum_{i = 0}^{N - 1} 2^i + 1 \cr
 &= -2^N + 2^N - 1 + 1 \cr
 &= 0 \cr
}
$$

Some architectures have direct instructions to do that, like the [movxs](http://www.c-jump.com/CIS77/ASM/DataTypes/T77_0270_sext_example_movsx.htm) in x86, other instead
[use multiple operations to do the same]({% post_url 2018-03-04-reversing-avr-code %}#sign-extension)

## Flags

It's all fine and good but as already said, we have a limited number of bits
to represent numbers, so it's possible that some operations couldn't be done
correctly: for example, if you want to sum, in a 8bits-register ``0xff`` to
any other number, you can't fit the result in the register, you should have
one bit more; for this reason in a CPU you have also some flags (i.e. one-bit
values) usually contained in an unique register to indicate some particular
properties of the last arithmetic operation. Take in mind that [not all
architectures have it](https://en.wikipedia.org/wiki/Status_register#CPU_architectures_without_arithmetic_flags).

Each system has its own nomenclature and specific flags, but I think the minimal
set is composed of the following

### Carry flag

Used in unsigned numbers to indicate that the result doesn't fit in the register.

### Overflow flag

Used for signed numbers to indicate that the resulting sign bit is not coherent
with the correct result; for example with 4-bit numbers we can have the
following four cases:

$$
\eqalign{
    0100 + 0100 &= 1000 \quad\hbox{overflow} \cr
    1000 + 1000 &= 0000 \quad\hbox{overflow} \cr
    0100 + 0001 &= 0101 \quad\hbox{no overflow} \cr
    1100 + 1100 &= 1000 \quad\hbox{no overflow} \cr
}
$$

### Zero flag

## Programmation errors

### Out of bounds

### Signedness

### Overflow

### Wrap

## Links

 - [The CARRY flag and OVERFLOW flag in binary arithmetic](http://teaching.idallen.com/dat2343/10f/notes/040_overflow.txt)
 - [Intel x86 JUMP quick reference](http://unixwiz.net/techtips/x86-jumps.html)
 - [SEI CERT C Coding Standard](https://wiki.sei.cmu.edu/confluence/display/c/SEI+CERT+C+Coding+Standard)