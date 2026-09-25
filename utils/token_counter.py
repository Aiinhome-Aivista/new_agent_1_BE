total_prompt_tokens = 0
total_completion_tokens = 0
total_tokens = 0

def add_tokens(prompt, completion, total):
    global total_prompt_tokens, total_completion_tokens, total_tokens
    total_prompt_tokens += prompt
    total_completion_tokens += completion
    total_tokens += total
    
    print(f"")
    print(f"==================================================")
    print(f"[CUMULATIVE TOKEN USAGE] Prompt: {total_prompt_tokens} | Completion: {total_completion_tokens} | Total: {total_tokens}")
    print(f"==================================================")
    print(f"")
