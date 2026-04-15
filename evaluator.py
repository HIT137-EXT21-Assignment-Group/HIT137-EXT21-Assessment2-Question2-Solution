"""
evaluator.py – Mathematical Expression Evaluator

Reads mathematical expressions from a text file (one per line), tokenises,
parses via recursive descent, evaluates, and writes structured output.

Grammar (by descending precedence):
    expression  → term   ( ('+' | '-') term   )*
    term        → unary  ( ('*' | '/') unary  )*
    unary       → '-' unary | primary
    primary     → '(' expression ')' | NUMBER
    implicit    → handled by inserting '*' between adjacent tokens where
                  multiplication is implied (e.g. 2(3) or (2)(3))

Token types: NUM, OP, LPAREN, RPAREN, END

Author : Saugat Poudel, Aseem Neupane
Student ID: s395696, s396016
"""

from __future__ import annotations

import os
import re
from typing import Optional


# ---------------------------------------------------------------------------
# 1. Tokeniser
# ---------------------------------------------------------------------------

# Each token is a simple dict: {"type": str, "value": str}

def _make_token(tok_type: str, value: str) -> dict:
    """Create a token dictionary."""
    return {"type": tok_type, "value": value}


def tokenise(expression: str) -> list[dict]:
    """
    Convert a raw expression string into a list of token dicts.

    Raises ValueError on illegal characters or unsupported unary '+'.

    Unary negation is represented as a separate OP '-' token; it is *not*
    folded into the number literal (per specification).

    Implicit multiplication is detected and an explicit '*' OP token is
    inserted wherever two adjacent tokens imply multiplication, e.g.
        2(3)  →  2 * (3)
        (2)(3) → (2) * (3)
        5 3    →  5 * 3
    """
    tokens: list[dict] = []
    i = 0
    length = len(expression)

    while i < length:
        ch = expression[i]

        # --- whitespace ---
        if ch.isspace():
            i += 1
            continue

        # --- number literal (integer or decimal) ---
        if ch.isdigit() or (ch == '.' and i + 1 < length and expression[i + 1].isdigit()):
            start = i
            while i < length and (expression[i].isdigit() or expression[i] == '.'):
                i += 1
            num_str = expression[start:i]
            # Validate: at most one decimal point
            if num_str.count('.') > 1:
                raise ValueError(f"Invalid number literal: {num_str}")
            tokens.append(_make_token("NUM", num_str))
            continue

        # --- operators ---
        if ch in ('+', '-', '*', '/'):
            # Detect unsupported unary '+'
            if ch == '+':
                if _is_unary_position(tokens):
                    raise ValueError("Unary + is not supported")
            tokens.append(_make_token("OP", ch))
            i += 1
            continue

        # --- parentheses ---
        if ch == '(':
            tokens.append(_make_token("LPAREN", "("))
            i += 1
            continue
        if ch == ')':
            tokens.append(_make_token("RPAREN", ")"))
            i += 1
            continue

        # --- anything else is an error ---
        raise ValueError(f"Unexpected character: '{ch}'")

    # Insert implicit multiplication tokens
    tokens = _insert_implicit_multiplication(tokens)

    tokens.append(_make_token("END", ""))
    return tokens


def _is_unary_position(tokens: list[dict]) -> bool:
    """
    Return True if the current position is a *unary* context, i.e. there is
    no preceding operand (the operator appears at the start, after '(', or
    after another operator).
    """
    if not tokens:
        return True
    prev = tokens[-1]
    return prev["type"] in ("OP", "LPAREN")


def _insert_implicit_multiplication(tokens: list[dict]) -> list[dict]:
    """
    Walk through the token list and insert an explicit '*' OP token between
    any two adjacent tokens that imply multiplication.

    Implicit multiplication occurs when a token that *ends* an operand
    (NUM or RPAREN) is immediately followed by a token that *begins* an
    operand (NUM or LPAREN).
    """
    if len(tokens) <= 1:
        return tokens

    result: list[dict] = [tokens[0]]
    ends_operand = {"NUM", "RPAREN"}
    begins_operand = {"NUM", "LPAREN"}

    for tok in tokens[1:]:
        if result[-1]["type"] in ends_operand and tok["type"] in begins_operand:
            result.append(_make_token("OP", "*"))
        result.append(tok)

    return result


# ---------------------------------------------------------------------------
# 2. Formatting helpers
# ---------------------------------------------------------------------------

def format_tokens(tokens: list[dict]) -> str:
    """
    Produce the tokens line, e.g. '[NUM:3] [OP:+] [NUM:5] [END]'.
    """
    parts = []
    for tok in tokens:
        if tok["type"] == "END":
            parts.append("[END]")
        else:
            parts.append(f"[{tok['type']}:{tok['value']}]")
    return " ".join(parts)


def format_result(value: float) -> str:
    """
    Format a numeric result: whole numbers without a decimal point,
    otherwise rounded to 4 decimal places.
    """
    if value == int(value):
        return str(int(value))
    return f"{value:.4f}"


# ---------------------------------------------------------------------------
# 3. Recursive-descent parser  →  expression tree (nested tuples)
#
#    Tree node representations:
#        number   → float value   (a plain float)
#        binary   → ("op", left, right)
#        negation → ("neg", operand)
# ---------------------------------------------------------------------------

class _Parser:
    """
    Stateful recursive-descent parser.  Implemented as a lightweight object
    (not a user-facing class) so that the position cursor is shared naturally
    across the mutually recursive grammar functions.
    """

    def __init__(self, tokens: list[dict]) -> None:
        self.tokens = tokens
        self.pos = 0

    # -- helper methods -----------------------------------------------------

    def _current(self) -> dict:
        """Return the current token without advancing."""
        return self.tokens[self.pos]

    def _advance(self) -> dict:
        """Return the current token and advance the cursor."""
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, tok_type: str) -> dict:
        """Consume a token of the given type or raise an error."""
        tok = self._current()
        if tok["type"] != tok_type:
            raise ValueError(
                f"Expected {tok_type}, got {tok['type']}:{tok['value']}"
            )
        return self._advance()

    # -- grammar rules ------------------------------------------------------

    def parse(self):
        """Entry point: parse a full expression and ensure all input consumed."""
        tree = self._expression()
        self._expect("END")
        return tree

    def _expression(self):
        """expression → term ( ('+' | '-') term )*"""
        left = self._term()
        while (self._current()["type"] == "OP"
               and self._current()["value"] in ("+", "-")):
            op = self._advance()["value"]
            right = self._term()
            left = (op, left, right)
        return left

    def _term(self):
        """term → unary ( ('*' | '/') unary )*"""
        left = self._unary()
        while (self._current()["type"] == "OP"
               and self._current()["value"] in ("*", "/")):
            op = self._advance()["value"]
            right = self._unary()
            left = (op, left, right)
        return left

    def _unary(self):
        """unary → '-' unary | primary"""
        if (self._current()["type"] == "OP"
                and self._current()["value"] == "-"):
            self._advance()  # consume '-'
            operand = self._unary()
            return ("neg", operand)
        return self._primary()

    def _primary(self):
        """primary → '(' expression ')' | NUMBER"""
        tok = self._current()
        if tok["type"] == "LPAREN":
            self._advance()  # consume '('
            node = self._expression()
            self._expect("RPAREN")
            return node
        if tok["type"] == "NUM":
            self._advance()
            return float(tok["value"])
        raise ValueError(f"Unexpected token: {tok['type']}:{tok['value']}")


def parse(tokens: list[dict]):
    """
    Public helper: parse a token list into an expression tree.

    Returns the tree root (float | tuple).
    """
    return _Parser(tokens).parse()


# ---------------------------------------------------------------------------
# 4. Tree formatting  →  string
# ---------------------------------------------------------------------------

def format_tree(node) -> str:
    """
    Convert an expression-tree node to its display string.

    • number  → formatted value (e.g. '3', '2.5')
    • binary  → '(op left right)'
    • neg     → '(neg operand)'
    """
    if isinstance(node, (int, float)):
        return format_result(node)
    op = node[0]
    if op == "neg":
        return f"(neg {format_tree(node[1])})"
    # binary
    left_str = format_tree(node[1])
    right_str = format_tree(node[2])
    return f"({op} {left_str} {right_str})"


# ---------------------------------------------------------------------------
# 5. Evaluator
# ---------------------------------------------------------------------------

def evaluate(node) -> float:
    """
    Recursively evaluate an expression tree, returning a float.

    Raises ZeroDivisionError on division by zero.
    """
    if isinstance(node, (int, float)):
        return float(node)

    op = node[0]

    if op == "neg":
        return -evaluate(node[1])

    left_val = evaluate(node[1])
    right_val = evaluate(node[2])

    if op == "+":
        return left_val + right_val
    if op == "-":
        return left_val - right_val
    if op == "*":
        return left_val * right_val
    if op == "/":
        if right_val == 0:
            raise ZeroDivisionError("Division by zero")
        return left_val / right_val

    raise ValueError(f"Unknown operator: {op}")


# ---------------------------------------------------------------------------
# 6. Top-level driver
# ---------------------------------------------------------------------------

def _process_expression(expr: str) -> dict:
    """
    Process a single expression string through tokenise → parse → evaluate.

    Returns a dict with keys: input, tree, tokens, result.
    On any error the tree/tokens/result fields are set to "ERROR".
    """
    tokens_str = "ERROR"
    tree_str = "ERROR"
    result_out = "ERROR"

    try:
        tokens = tokenise(expr)
        tokens_str = format_tokens(tokens)
    except Exception:
        return {"input": expr, "tree": "ERROR", "tokens": "ERROR", "result": "ERROR"}

    try:
        tree = parse(tokens)
        tree_str = format_tree(tree)
    except Exception:
        return {"input": expr, "tree": "ERROR", "tokens": tokens_str, "result": "ERROR"}

    try:
        result_val = evaluate(tree)
        result_out = result_val
    except Exception:
        result_out = "ERROR"

    return {"input": expr, "tree": tree_str, "tokens": tokens_str, "result": result_out}


def evaluate_file(input_path: str) -> list[dict]:
    """
    Read expressions from *input_path* (one per line), evaluate each one,
    write 'output.txt' to the same directory, and return a list of result
    dicts.

    Each dict has the keys: input, tree, tokens, result.
    'result' is a float on success or the string "ERROR" on failure.
    'tree' and 'tokens' are strings.
    """
    # Read input lines, stripping trailing whitespace / newlines
    with open(input_path, "r") as fh:
        lines = [line.rstrip("\n\r") for line in fh if line.strip()]

    results: list[dict] = []
    for line in lines:
        results.append(_process_expression(line))

    # Write output.txt in the same directory as the input file
    output_path = os.path.join(os.path.dirname(input_path), "output.txt")
    with open(output_path, "w") as fh:
        for i, entry in enumerate(results):
            fh.write(f"Input: {entry['input']}\n")
            fh.write(f"Tree: {entry['tree']}\n")
            fh.write(f"Tokens: {entry['tokens']}\n")
            if entry["result"] == "ERROR":
                fh.write("Result: ERROR\n")
            else:
                fh.write(f"Result: {format_result(entry['result'])}\n")
            if i < len(results) - 1:
                fh.write("\n")

    return results


# ---------------------------------------------------------------------------
# 7. Quick self-test when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Minimal smoke test
    sample = "sample_input.txt"
    if os.path.exists(sample):
        results = evaluate_file(sample)
        for r in results:
            print(r)
    else:
        print("No sample_input.txt found; provide one to test.")
