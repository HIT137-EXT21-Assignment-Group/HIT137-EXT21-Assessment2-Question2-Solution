# Mathematical Expression Evaluator

A command-line Python tool that reads mathematical expressions from a text file, tokenises and parses them via a recursive-descent parser, evaluates the results, and writes structured output — complete with token streams and expression trees.

**HIT137 — EXT21 | Assessment 2 | Group Assignment**
**Authors:** Saugat Poudel (s395696) · Aseem Neupane (s396016)

---

## Features

* Tokenises expressions into typed tokens (`NUM`, `OP`, `LPAREN`, `RPAREN`, `END`)
* Builds an expression tree via recursive-descent parsing with correct operator precedence
* Supports:

  * Basic arithmetic: `+`, `-`, `*`, `/`
  * Unary negation: `-x`, `--x`
  * Nested parentheses: `(10 - 2) * 3`
  * Implicit multiplication: `2(3)`, `(2)(3)`
  * Decimal numbers: `3.14 * 2`
* Graceful error handling for:

  * Division by zero
  * Illegal characters (e.g. `@`, `#`)
  * Unsupported unary `+`
* Outputs a structured `output.txt` with input, token stream, tree, and result for every expression

---

## Project Structure

```
assessment2_solution/
├── evaluator.py        # Main source file
├── sample_input.txt    # Input expressions (one per line)
├── output.txt          # Auto-generated output
└── README.md
```

---

## Getting Started

### Prerequisites

* Python 3.8 or higher
* No external dependencies — standard library only

### Installation

```bash
git clone https://github.com/HIT137-EXT21-Assignment-Group/HIT137-EXT21-Assessment2-Question2-Solution.git
cd HIT137-EXT21-Assessment2-Question2-Solution
```

---

## Usage

Create a `sample_input.txt` file with one expression per line:

```
3 + 5
2 + 3 * 4
-(3 + 4)
--5
(10 - 2) * 3 + -4 / 2
3 @ 5
1 / 0
```

Run the evaluator:

```bash
python3 evaluator.py
```

Results are printed to the terminal and saved to `output.txt` in the same directory.

---

## Sample Output

```
Input: 3 + 5
Tree: (+ 3 5)
Tokens: [NUM:3] [OP:+] [NUM:5] [END]
Result: 8

Input: 2 + 3 * 4
Tree: (+ 2 (* 3 4))
Tokens: [NUM:2] [OP:+] [NUM:3] [OP:*] [NUM:4] [END]
Result: 14

Input: -(3 + 4)
Tree: (neg (+ 3 4))
Tokens: [OP:-] [LPAREN:(] [NUM:3] [OP:+] [NUM:4] [RPAREN:)] [END]
Result: -7

Input: --5
Tree: (neg (neg 5))
Tokens: [OP:-] [OP:-] [NUM:5] [END]
Result: 5

Input: (10 - 2) * 3 + -4 / 2
Tree: (+ (* (- 10 2) 3) (/ (neg 4) 2))
Tokens: [LPAREN:(] [NUM:10] [OP:-] [NUM:2] [RPAREN:)] [OP:*] [NUM:3] [OP:+] [OP:-] [NUM:4] [OP:/] [NUM:2] [END]
Result: 22

Input: 3 @ 5
Tree: ERROR
Tokens: ERROR
Result: ERROR

Input: 1 / 0
Tree: (/ 1 0)
Tokens: [NUM:1] [OP:/] [NUM:0] [END]
Result: ERROR
```

---

## Grammar

The parser implements the following grammar (in descending order of precedence):

```
expression  →  term   ( ('+' | '-') term   )*
term        →  unary  ( ('*' | '/') unary  )*
unary       →  '-' unary | primary
primary     →  '(' expression ')' | NUMBER
```

Implicit multiplication (e.g. `2(3)`) is resolved during tokenisation by inserting an explicit `*` token between adjacent operands.

---

## Architecture Overview

| Module                            | Responsibility                                             |
| --------------------------------- | ---------------------------------------------------------- |
| tokenise()                        | Lexical analysis — converts raw string into typed tokens   |
| _insert_implicit_multiplication() | Detects and inserts implied `*` tokens                     |
| Parser class                      | Recursive-descent parser — builds an expression tree       |
| evaluate()                        | Tree-walking evaluator — computes the final numeric result |
| format_tree()                     | Serialises the expression tree to a readable string        |
| evaluate_file()                   | Top-level driver — reads input file, writes output file    |

---

## Error Handling

| Scenario                       | Behaviour                                    |
| ------------------------------ | -------------------------------------------- |
| Illegal character (e.g. `@`)   | tokens: ERROR, tree: ERROR, result: ERROR    |
| Malformed number (e.g. `3..5`) | tokens: ERROR, tree: ERROR, result: ERROR    |
| Unary `+`                      | tokens: ERROR, tree: ERROR, result: ERROR    |
| Parse error                    | tokens preserved, tree: ERROR, result: ERROR |
| Division by zero               | tokens and tree preserved, result: ERROR     |

Errors are isolated per expression — one bad line does not affect the rest.

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.
