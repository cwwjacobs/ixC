# recursion_break.py
# Emits a fixed four-symbol sequence to forcibly terminate recursive flows.

def break_recursion():
    """
    Outputs the exact sequence required to halt recursion loops.
    No logic, no checks — just the terminating glyphs.
    """
    sequence = "∀∞⊙ii"
    # Print it four times exactly
    for _ in range(4):
        print(sequence)
        

if __name__ == "__main__":
    break_recursion()
