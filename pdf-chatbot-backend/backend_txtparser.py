def parse_generated_questions(raw_text, question_type):
    import re
    questions = []

    if question_type == 'multiple-choice':
        # Split into blocks per question
        question_blocks = re.split(r'\n(?=Question\s+\d+:)', raw_text)
        question_id = 1

        for block in question_blocks:
            lines = block.strip().split('\n')
            if not lines or not lines[0].lower().startswith("question"):
                continue

            # Extract question text
            question_line = lines[0]
            question_text = question_line.split(":", 1)[-1].strip()

            options = []
            correct_answer = None

            # Process the rest of the lines
            for line in lines[1:]:
                line = line.strip()
                # Detect answer line
                if line.lower().startswith("answer"):
                    match = re.search(r'([A-D])\)', line)
                    if match:
                        answer_letter = match.group(1)
                        for opt in options:
                            if opt.startswith(f"{answer_letter})") or opt.startswith(f"{answer_letter}."):
                                correct_answer = re.sub(r'^[A-D][).]\s*', '', opt)
                                break
                # Detect options
                elif re.match(r"^[A-D][).]\s", line):
                    options.append(line)

            # Clean options (strip A), B), etc.)
            cleaned_options = [re.sub(r"^[A-D][).]\s*", "", opt) for opt in options]

            # Fallback: if no answer parsed, default to first option
            if not correct_answer and cleaned_options:
                correct_answer = cleaned_options[0]

            questions.append({
                "id": question_id,
                "question": question_text,
                "options": cleaned_options,
                "correctAnswer": correct_answer
            })
            question_id += 1
    
    elif question_type == 'true-false':
        # Parse true/false questions
        question_blocks = re.split(r'\s*Question\s+\d+:\s*', raw_text)
        question_blocks = [q.strip() for q in question_blocks if q.strip()]
    
        question_id = 1
        for block in question_blocks:
            parts = re.split(r'\s*Answer:\s*', block, maxsplit=1)
            question_text = parts[0].strip()
    
            if len(parts) == 2:
                answer_text = parts[1].strip().lower()
                if answer_text == "true":
                    correct_answer = True
                elif answer_text == "false":
                    correct_answer = False
                else:
                    correct_answer = None  # or maybe raise an error
            else:
                correct_answer = None
    
            questions.append({
                "id": question_id,
                "question": question_text,
                "options": ["True", "False"],
                "correctAnswer": correct_answer
            })
            question_id += 1


    elif question_type == 'open-ended':
        # Parse open-ended questions
        # Split by "Question X:"
        question_blocks = re.split(r'\s*Question\s+\d+:\s*', raw_text)
        question_blocks = [q.strip() for q in question_blocks if q.strip()]

        question_id = 1
        for block in question_blocks:
            # Look for "Answer: ..." separator
            parts = re.split(r'\s*Answer:\s*', block, maxsplit=1)
            if len(parts) == 2:
                question_text = parts[0].strip()
                answer_text = parts[1].strip()
            else:
                question_text = block.strip()
                answer_text = ""

            questions.append({
                "id": question_id,
                "question": question_text,
                "answer": answer_text
            })
            question_id += 1

    return questions
