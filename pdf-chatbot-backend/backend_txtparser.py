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

        return questions
