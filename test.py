import re
import os

def tokenize(expression):
    """Uses regex to extract all tokens from the expression."""
    # Pattern handles numbers (with decimals), operators, and parentheses
    pattern = r"\d+\.?\d*|[\+\-\*\/\(\)]"
    matches = re.findall(pattern, expression)
    
    # Check for invalid characters by comparing reconstructed string
    if len("".join(re.findall(r"\s+", expression))) + len("".join(matches)) != len(expression):
        return None
        
    tokens = []
    for m in matches:
        if m.isdigit() or ('.' in m and m.replace('.', '', 1).isdigit()):
            tokens.append(("NUM", m))
        elif m in "+-*/":
            tokens.append(("OP", m))
        elif m == '(':
            tokens.append(("LPAREN", "("))
        elif m == ')':
            tokens.append(("RPAREN", ")"))
            
    tokens.append(("END", "END"))
    return tokens

def format_tokens_string(tokens):
    """Formats the token list for the output file requirements[cite: 55]."""
    if tokens is None:
        return "ERROR"
    return " ".join([f"[{t[0]}:{t[1]}]" if t[0] != "END" else "[END]" for t in tokens])

def evaluate_file(input_path: str) -> list[dict]:
    """Reads expressions from file and writes results to output.txt[cite: 60, 62]."""
    results_list = []
    
    if not os.path.exists(input_path):
        return []

    with open(input_path, 'r') as f:
        lines = f.readlines()

    # Determine output path using os.path [cite: 43]
    output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, "output.txt")

    with open(output_path, 'w') as out_f:
        for idx, line in enumerate(lines):
            raw_input = line.strip()
            tokens = tokenize(raw_input)
            
            pos = 0
            error_occured = False

            def peek():
                return tokens[pos] if tokens and pos < len(tokens) else ("END", "END")

            def consume():
                nonlocal pos
                item = peek()
                pos += 1
                return item

            def parse_expression():
                """Handles Addition and Subtraction[cite: 36, 38]."""
                node_tree, val = parse_term()
                while peek()[1] in ('+', '-'):
                    op = consume()[1]
                    right_tree, right_val = parse_term()
                    node_tree = f"({op} {node_tree} {right_tree})"
                    if val != "ERROR" and right_val != "ERROR":
                        val = (val + right_val) if op == '+' else (val - right_val)
                    else:
                        val = "ERROR"
                return node_tree, val

            def parse_term():
                """Handles Multiplication, Division, and Implicit Multiplication[cite: 41, 48]."""
                node_tree, val = parse_factor()
                while True:
                    nxt_type, nxt_val = peek()
                    if nxt_val in ('*', '/'):
                        op = consume()[1]
                        right_tree, right_val = parse_factor()
                        node_tree = f"({op} {node_tree} {right_tree})"
                        if val != "ERROR" and right_val != "ERROR":
                            if op == '*':
                                val *= right_val
                            else:
                                val = val / right_val if right_val != 0 else "ERROR"
                        else:
                            val = "ERROR"
                    elif nxt_type in ("NUM", "LPAREN"): 
                        # Logic for Implicit Multiplication [cite: 41]
                        right_tree, right_val = parse_factor()
                        node_tree = f"(* {node_tree} {right_tree})"
                        val = (val * right_val) if (val != "ERROR" and right_val != "ERROR") else "ERROR"
                    else:
                        break
                return node_tree, val

            def parse_factor():
                """Handles Unary Negation and Parentheses[cite: 38, 48]."""
                nonlocal error_occured
                t_type, t_val = peek()
                
                if t_val == '-':
                    consume()
                    tree, val = parse_factor()
                    # Negation displayed as (neg operand) [cite: 48]
                    return f"(neg {tree})", (-val if isinstance(val, (int, float)) else "ERROR")
                
                if t_val == '+': # Unary + is not supported [cite: 39]
                    error_occured = True
                    return "ERROR", "ERROR"

                if t_type == "NUM":
                    val = float(consume()[1])
                    # Formatting number literal for tree [cite: 46]
                    tree_val = str(int(val)) if val.is_integer() else str(val)
                    return tree_val, val
                
                if t_type == "LPAREN":
                    consume()
                    tree, val = parse_expression()
                    if consume()[0] != "RPAREN":
                        error_occured = True
                    return tree, val
                
                error_occured = True
                return "ERROR", "ERROR"

            # Parse the tokens
            if tokens is None:
                tree_str, result, token_str = "ERROR", "ERROR", "ERROR"
            else:
                tree_str, result = parse_expression()
                if peek()[0] != "END" or error_occured:
                    tree_str, result = "ERROR", "ERROR"
                token_str = format_tokens_string(tokens)

            # Final result formatting [cite: 56, 57]
            if isinstance(result, (int, float)):
                display_res = str(int(result)) if result.is_integer() else f"{result:.4f}".rstrip('0').rstrip('.')
            else:
                display_res = "ERROR"

            # Write formatted block to output.txt [cite: 44, 52]
            out_f.write(f"Input: {raw_input}\nTree: {tree_str}\nTokens: {token_str}\nResult: {display_res}\n\n")

            results_list.append({
                "input": raw_input,
                "tree": tree_str,
                "tokens": token_str,
                "result": result if result == "ERROR" else float(result)
            })
            
    return results_list

if __name__ == "__main__":
    # Minimal smoke test
    sample = "sample_input.txt"
    if os.path.exists(sample):
        results = evaluate_file(sample)
        for r in results:
            print(r)
    else:
        print("No sample_input.txt found; provide one to test.")
