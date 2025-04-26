def parse_generated_questions(raw_text, question_type):
    """
    Parse the raw text output from LLM into structured question data based on the question type.
    
    Args:
        raw_text (str): Raw text output from the LLM
        question_type (str): Type of questions (multiple-choice, true-false, open-ended)
        
    Returns:
        list: List of structured question objects
    """
    questions = []
    
    # Clean up the text
    lines = raw_text.replace('\r', '').split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    if question_type == 'multiple-choice':
        current_question = None
        question_text = None
        options = []
        correct_answer = None
        question_id = 1
        
        for line in lines:
            # Check if line starts with number followed by period or question mark (new question)
            if (line[0].isdigit() and ('. ' in line[:5] or '? ' in line[:5])) or (len(questions) == 0 and line):
                # Save previous question if exists
                if current_question is not None:
                    questions.append({
                        "id": question_id,
                        "question": question_text,
                        "options": options,
                        "correctAnswer": correct_answer
                    })
                    question_id += 1
                
                # Start new question
                current_question = line
                
                # Try to extract the question text
                parts = line.split(')')
                if len(parts) > 1:
                    # Format: 1) What is...
                    question_text = parts[0].split('.', 1)[-1].strip() + ')'
                    for part in parts[1:]:
                        question_text += part
                else:
                    # Format: 1. What is...
                    question_text = line.split('.', 1)[-1].strip() if '.' in line else line
                
                # Reset options and correct answer
                options = []
                correct_answer = None
            
            # Check if line contains options (A, B, C, D)
            elif any(opt in line for opt in ['A)', 'B)', 'C)', 'D)', 'A.', 'B.', 'C.', 'D.']):
                # Parse options
                option_text = line.strip()
                options.append(option_text)
            
            # Check if line contains answer information
            elif 'answer' in line.lower() or 'correct' in line.lower():
                # Extract correct answer
                answer_part = line.lower().split('answer', 1)[-1].strip()
                if ':' in answer_part:
                    answer_letter = answer_part.split(':', 1)[-1].strip()[0].upper()
                    
                    # Match the answer letter to the full text of the option
                    for option in options:
                        if option.startswith(f"{answer_letter})") or option.startswith(f"{answer_letter}."):
                            correct_answer = option.split(')', 1)[-1].strip() if ')' in option else option.split('.', 1)[-1].strip()
                            break
        
        # Add the last question
        if current_question is not None and question_text is not None:
            # Extract options from the question text if they're embedded
            if not options and ('A)' in question_text or 'A.' in question_text):
                # Split the text to extract embedded options
                option_parts = question_text.split('A)', 1) if 'A)' in question_text else question_text.split('A.', 1)
                if len(option_parts) > 1:
                    question_text = option_parts[0].strip()
                    option_text = 'A)' + option_parts[1] if 'A)' in question_text else 'A.' + option_parts[1]
                    
                    # Further split the options
                    option_segments = []
                    for marker in ['B)', 'C)', 'D)', 'B.', 'C.', 'D.']:
                        if marker in option_text:
                            segments = option_text.split(marker)
                            option_segments.append(segments[0].strip())
                            option_text = marker + segments[1]
                    option_segments.append(option_text.strip())
                    
                    options = option_segments
            
            # Ensure we have a correct answer, default to first option if not specified
            if not correct_answer and options:
                correct_answer = options[0].split(')', 1)[-1].strip() if ')' in options[0] else options[0].split('.', 1)[-1].strip()
            
            # Clean up options to remove option indicators (A), B), etc.)
            cleaned_options = []
            for option in options:
                if ')' in option[:3] or '.' in option[:3]:
                    cleaned_options.append(option[2:].strip())
                else:
                    cleaned_options.append(option)
            
            questions.append({
                "id": question_id,
                "question": question_text,
                "options": cleaned_options,
                "correctAnswer": correct_answer
            })
    
    elif question_type == 'true-false':
        question_id = 1
        
        for line in lines:
            # Skip lines that don't look like questions
            if not any(char.isdigit() for char in line[:3]):
                continue
                
            # Split into question and answer if possible
            if 'answer' in line.lower() or 'true' in line.lower() or 'false' in line.lower():
                # Try to split by common patterns
                question_text = None
                correct_answer = None
                
                # Pattern: "1. Question text (True/False)"
                if '(' in line and (')' in line or '.)' in line):
                    parts = line.split('(')
                    question_text = parts[0].split('.', 1)[-1].strip() if '.' in parts[0] else parts[0]
                    answer_part = parts[1].split(')')[0].lower()
                    correct_answer = 'true' in answer_part
                
                # Pattern: "1. Question text. Answer: True/False"
                elif 'answer' in line.lower():
                    parts = line.lower().split('answer')
                    question_text = parts[0].split('.', 1)[-1].strip() if '.' in parts[0] else parts[0]
                    answer_part = parts[1].strip()
                    if ':' in answer_part:
                        answer_part = answer_part.split(':', 1)[-1].strip()
                    correct_answer = 'true' in answer_part
                
                # If we couldn't parse, just split by period
                if question_text is None:
                    # Just assume the statement and try to find answer indication
                    question_text = line.split('.', 1)[-1].strip() if '.' in line else line
                    correct_answer = 'true' in line.lower() and not ('not true' in line.lower() or 'isn\'t true' in line.lower())
                
                questions.append({
                    "id": question_id,
                    "question": question_text,
                    "correctAnswer": correct_answer
                })
                question_id += 1
    
    elif question_type == 'open-ended':
        current_question = None
        current_answer = None
        question_id = 1
        collecting_answer = False
        
        for line in lines:
            # Check if this is a new question
            if (line[0].isdigit() and ('.' in line[:5] or '?' in line[:5])) or (len(questions) == 0 and not collecting_answer):
                # Save previous Q&A pair if exists
                if current_question is not None and current_answer is not None:
                    questions.append({
                        "id": question_id,
                        "question": current_question,
                        "answer": current_answer
                    })
                    question_id += 1
                
                # Start new question
                current_question = line.split('.', 1)[-1].strip() if '.' in line[:5] else line
                current_answer = None
                collecting_answer = False
            
            # Check if this is an answer indicator
            elif ('answer' in line.lower() or 'explanation' in line.lower() or 'response' in line.lower()) and not collecting_answer:
                collecting_answer = True
                current_answer = line.split(':', 1)[-1].strip() if ':' in line else ""
            
            # Add to the current answer if we're collecting it
            elif collecting_answer:
                if current_answer:
                    current_answer += " " + line
                else:
                    current_answer = line
            
            # If not a new question or answer indicator, it's part of the current question
            elif current_question is not None and not collecting_answer:
                current_question += " " + line
        
        # Add the last Q&A pair
        if current_question is not None:
            # If we never found an answer section, assume everything after the question is the answer
            if current_answer is None:
                parts = raw_text.split(current_question, 1)
                if len(parts) > 1:
                    current_answer = parts[1].strip()
                else:
                    current_answer = "No answer provided."
            
            questions.append({
                "id": question_id,
                "question": current_question,
                "answer": current_answer
            })
    
    return questions