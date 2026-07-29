import os

def move_case_study_slides():
    filepath = r"d:\Agent1New\PWC_agent\new_agent_1_BE\utils\pptx_generator.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    target_idx = -1
    
    for i, line in enumerate(lines):
        if "# SLIDE 5B: Case Study" in line:
            start_idx = i - 1 # Include the previous comment line
        if "# SLIDE 6: Effort & Person-Hour Conversion" in line:
            end_idx = i - 1
        if "# Slide 10: Thank You Slide" in line:
            target_idx = i
            
    if start_idx != -1 and end_idx != -1 and target_idx != -1:
        # Extract the block
        case_study_block = lines[start_idx:end_idx]
        
        # Remove from original location
        del lines[start_idx:end_idx]
        
        # Recalculate target index because we removed lines before it
        target_idx -= (end_idx - start_idx)
        
        # Insert at new location
        lines = lines[:target_idx] + case_study_block + lines[target_idx:]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("Successfully moved the case study block.")
    else:
        print(f"Failed to find indices. Start: {start_idx}, End: {end_idx}, Target: {target_idx}")

if __name__ == "__main__":
    move_case_study_slides()
