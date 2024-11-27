section .data
    welcome     db 'Hi! We are Francis, Rein, Jeremy and Ean. This program is intended to sort numbers', 13, 10
                db 'and words or change all the vowels to a number.', 13, 10, 13, 0
    menu        db 10,'==== Assembly Program by Francis, Rein, Jeremy and Ean ===', 13, 10
                db 10, '[0] Exit', 13, 10
                db '[1] Number', 13, 10
                db '[2] Word', 13, 10, 0
    
    ARRAY_SIZE  equ 5
    WORD_SIZE   equ 20
    
    fmt_int     db '%d', 0 
    fmt_str     db '%s', 0
    fmt_char    db '%c', 0
    newline     db 13, 10, 0
    
    prompt_choice   db 'Enter choice: ', 0
    prompt_items    db 10, 'Enter up to 5 items:', 13, 10, 0
    prompt_sort     db 10,'Sort by [1] Ascending or [2] Descending: ', 0
    prompt_vowels   db 10, 'Do you want to change the vowels? (Y/N): ', 0
    sorted_header   db 10, 'Sorted items:', 13, 10, 0
    changed_header  db 10, 'Changed vowels:', 13, 10, 0
    goodbye         db 10, 'Thank you!', 13, 10, 0
    
    err_choice_input db 10, 'Error: Invalid input. Please select from the choices only.' ,13, 10, 0
    err_num_input   db 10, 'Error: Invalid input. Please enter only numbers.', 13, 10, 0
    err_word_input  db 10, 'Error: Invalid input. Please enter only words.', 13, 10, 0
    
    vowels          db 'aeiouAEIOU', 0
    vowel_nums      db '12345', 0

section .bss
    choice      resd 1
    sort_order  resd 1
    vowel_choice resb 2
    numbers     resd ARRAY_SIZE
    words       resb WORD_SIZE * ARRAY_SIZE
    temp_word   resb WORD_SIZE
    temp        resd 1

section .text
    global _main
    extern _printf, _scanf, _gets, _strcmp, _strlen, _exit, _getchar

_main:
    push welcome
    call _printf
    add esp, 4

main_loop:
    push menu
    call _printf
    add esp, 4

    push prompt_choice
    call _printf
    add esp, 4

    push choice
    push fmt_int
    call _scanf
    add esp, 8
    
    cmp eax, 1
    jne invalid_choice
    
    mov eax, [choice]
    cmp eax, 0
    je exit_program
    cmp eax, 1
    je number_mode
    cmp eax, 2
    je word_mode
    
invalid_choice:
    push err_choice_input
    call _printf
    add esp, 4
    jmp main_loop

number_mode:    
    call get_numbers
    test eax, eax
    jz main_loop
    
    call get_sort_order
    test eax, eax
    jz main_loop
    
    call sort_numbers
    call display_numbers
    jmp main_loop

get_numbers:
    xor ebx, ebx  ; Clear the counter for number of items

.start:
    push prompt_items
    call _printf
    add esp, 4

.loop:
    cmp ebx, ARRAY_SIZE
    jge .done   ; If we've reached the maximum numbers, exit the loop

    lea eax, [numbers + ebx*4]  ; Load the address for the number input
    push eax
    push fmt_int
    call _scanf
    add esp, 8

    ; Validate that the input is a valid number
    test eax, eax
    jz .invalid_input   ; If validation failed, go to invalid input handling

    ; Increment the counter if valid
    inc ebx
    jmp .loop

.invalid_input:
    push err_num_input
    call _printf
    add esp, 4

.clear_buffer:
    call _getchar
    cmp al, 10
    jne .clear_buffer

    xor ebx, ebx  ; Reset counter and try again
    jmp .start

.done:
    mov eax, 1
    ret

word_mode:
    call get_words
    test eax, eax
    jz main_loop
    
    call get_sort_order
    test eax, eax
    jz main_loop
    
    call sort_words
    call display_words
    
    ; Ask the user if they want to change vowels
    push prompt_vowels
    call _printf
    add esp, 4
    
    ; Repeatedly ask for a valid input for vowels
get_vowel_choice:
    push vowel_choice
    push fmt_str
    call _scanf
    add esp, 8
    
    ; Check if the input is valid ('Y' or 'N')
    mov al, [vowel_choice]
    or al, 32     ; Convert to lowercase for easy comparison (case insensitive)
    cmp al, 'y'    ; Check if 'y' or 'Y'
    je do_vowel_conversion
    cmp al, 'n'    ; Check if 'n' or 'N'
    je main_loop   ; If 'N', go back to the main loop
    
    ; If input is invalid, re-prompt for the vowel change choice
    push err_word_input
    call _printf
    add esp, 4
    jmp get_vowel_choice  ; Go back to asking for vowel choice

get_words:
    xor ebx, ebx              ; Clear the counter for the number of words

.start:
    ; Display prompt to enter up to 5 items
    push prompt_items
    call _printf
    add esp, 4

    ; Collect all inputs
.collect_loop:
    cmp ebx, ARRAY_SIZE       ; Check if we have entered 5 items
    jge .validate_all         ; If 5 items entered, proceed to validation

    mov eax, ebx
    imul eax, WORD_SIZE
    lea edi, [words + eax]    ; Calculate the address of the current word
    push edi
    push fmt_str
    call _scanf
    add esp, 8

    inc ebx                   ; Increment counter
    jmp .collect_loop         ; Repeat input collection

.validate_all:
    ; All inputs are collected, now validate each one
    xor ebx, ebx              ; Reset counter for validation

.validation_loop:
    cmp ebx, ARRAY_SIZE       ; Check if we have validated all 5 items
    jge .all_valid            ; If validation is complete, exit

    mov eax, ebx
    imul eax, WORD_SIZE
    lea esi, [words + eax]    ; Load the address of the current word
    push esi
    call validate_word        ; Validate the word (returns 1 if valid, 0 if invalid)
    add esp, 4
    test eax, eax             ; Check if the word is valid
    jz .invalid_input         ; If invalid, jump to input error handling

    inc ebx                   ; Increment the counter for next word
    jmp .validation_loop      ; Continue validating

.invalid_input:
    push err_word_input
    call _printf
    add esp, 4
    jmp .start                ; If any input is invalid, restart the input process

.all_valid:
    mov eax, 1                ; All inputs are valid
    ret



validate_word:
    ; Validate that the word contains only alphabetic characters (A-Z, a-z)
    xor eax, eax                ; Clear eax (return value, 0 = invalid, 1 = valid)
    mov esi, edi                ; EDI points to the start of the current word

validate_loop:
    mov al, [esi]               ; Load the character
    cmp al, 0                   ; Check if it's the null terminator (end of string)
    je validate_done            ; If it is, the word is valid

    ; Check if the character is a number
    cmp al, '0'
    jb .not_valid               ; If less than '0', not valid
    cmp al, '9'
    jbe .not_valid              ; If between '0' and '9', not valid

    ; Check if the character is a letter (A-Z or a-z)
    cmp al, 'A'
    jb .not_valid               ; If less than 'A', not valid
    cmp al, 'Z'
    jbe .check_next_char        ; If between 'A' and 'Z', valid character
    cmp al, 'a'
    jb .not_valid               ; If less than 'a', not valid
    cmp al, 'z'
    ja .not_valid               ; If greater than 'z', not valid

.check_next_char:
    inc esi                     ; Move to the next character
    jmp validate_loop

.not_valid:
    mov eax, 0                  ; Invalid input (non-alphabetic or numeric character found)
    ret

validate_done:
    mov eax, 1                  ; Valid input (only alphabetic characters)
    ret

get_sort_order:
    push prompt_sort
    call _printf
    add esp, 4
    
    push sort_order
    push fmt_int
    call _scanf
    add esp, 8
    
    ; Check if the user entered 1 or 2 for sorting order
    cmp dword [sort_order], 1
    je .valid_choice
    cmp dword [sort_order], 2
    je .valid_choice

    ; If the input is invalid, show error message
    push err_num_input
    call _printf
    add esp, 4
    jmp get_sort_order

.valid_choice:
    mov eax, 1
    ret

sort_numbers:
    mov ecx, ARRAY_SIZE - 1
    
outer_loop:
    push ecx
    xor ebx, ebx
    
inner_loop:
    mov eax, ebx
    shl eax, 2
    lea esi, [numbers + eax]
    lea edi, [esi + 4]
    
    mov eax, [esi]
    mov edx, [edi]
    
    push ebx
    mov ebx, [sort_order]
    cmp ebx, 1
    pop ebx
    je compare_ascending
    
compare_descending:
    cmp eax, edx
    jl swap_elements
    jmp continue_inner
    
compare_ascending:
    cmp eax, edx
    jg swap_elements
    jmp continue_inner
    
swap_elements:
    mov [temp], eax
    mov eax, [edi]
    mov [esi], eax
    mov eax, [temp]
    mov [edi], eax
    
continue_inner:
    inc ebx
    mov eax, ARRAY_SIZE
    sub eax, 1
    cmp ebx, eax
    jl inner_loop
    
    pop ecx
    loop outer_loop
    ret

sort_words:
    mov ecx, ARRAY_SIZE - 1
    
.outer_loop:
    push ecx
    xor ebx, ebx
    
.inner_loop:
    mov eax, ebx
    imul eax, WORD_SIZE
    lea esi, [words + eax]
    add eax, WORD_SIZE
    lea edi, [words + eax]
    
    push edi
    push esi
    call _strcmp
    add esp, 8
    
    mov edx, [sort_order]
    cmp edx, 1
    je .check_ascending
    
.check_descending:
    cmp eax, 0
    jge .continue_inner
    jmp .swap_words
    
.check_ascending:
    cmp eax, 0
    jle .continue_inner
    
.swap_words:
    push ecx
    push esi
    push edi
    
    mov ecx, WORD_SIZE
    mov esi, [esp+4]
    mov edi, temp_word
    rep movsb
    
    mov ecx, WORD_SIZE
    mov esi, [esp]
    mov edi, [esp+4]
    rep movsb
    
    mov ecx, WORD_SIZE
    mov esi, temp_word
    mov edi, [esp]
    rep movsb
    
    pop edi
    pop esi
    pop ecx
    
.continue_inner:
    inc ebx
    mov eax, ARRAY_SIZE
    sub eax, 1
    cmp ebx, eax
    jl .inner_loop
    
    pop ecx
    loop .outer_loop
    ret

do_vowel_conversion:
    push changed_header
    call _printf
    add esp, 4
    
    mov esi, words
    mov ecx, ARRAY_SIZE
    
.word_loop:
    push ecx
    
    push esi
    call convert_vowels
    add esp, 4
    
    push esi
    push fmt_str
    call _printf
    add esp, 8
    
    push newline
    call _printf
    add esp, 4
    
    add esi, WORD_SIZE
    pop ecx
    loop .word_loop
    jmp main_loop

convert_vowels:
    xor edx, edx                ; Clear the index register (EDX)
    mov ecx, WORD_SIZE          ; Set ECX to WORD_SIZE (max number of characters to check)

convert_loop:
    mov al, [esi + edx]         ; Load the current character of the word (pointed by ESI + EDX)
    cmp al, 0                   ; Check if it is the null terminator (end of word)
    je end_conversion           ; If it is, we are done
    
    ; Now, check if the character is a vowel
    mov ebx, vowels             ; EBX points to the vowels array
    mov edi, 0                  ; Index for vowels array
    
check_vowel:
    mov al, [ebx + edi]         ; Load the current vowel
    cmp al, [esi + edx]         ; Compare the vowel with the current character
    je replace_with_number      ; If it matches, replace it with a number
    
    inc edi                     ; Move to the next vowel in the array
    cmp byte [ebx + edi], 0     ; Check if we reached the end of the vowels string
    jne check_vowel             ; If not, continue checking the next vowel
    
    jmp next_char               ; If it's not a vowel, move to the next character

replace_with_number:
    ; Replace the vowel with a number from the vowel_nums array
    mov al, [vowel_nums + edi]  ; Load the corresponding number (1, 2, 3, 4, or 5)
    mov [esi + edx], al         ; Replace the vowel with the number

next_char:
    inc edx                     ; Move to the next character in the word
    cmp edx, WORD_SIZE          ; Check if we've reached the maximum word size
    jl convert_loop             ; If not, continue looping through the word

end_conversion:
    ret

display_numbers:
    push sorted_header
    call _printf
    add esp, 4
    
    xor ebx, ebx
    
display_loop:
    cmp ebx, ARRAY_SIZE
    jge display_done  ; this ends the display_numbers function
    
    mov eax, ebx
    shl eax, 2
    
    push dword [numbers + eax]
    push fmt_int
    call _printf
    add esp, 8
    
    push newline
    call _printf
    add esp, 4
    
    inc ebx
    jmp display_loop
    
display_done:
    ret

display_words:
    push sorted_header
    call _printf
    add esp, 4
    
    xor ebx, ebx
    
.display_loop:
    cmp ebx, ARRAY_SIZE
    jge display_words_done  ; new end label for display_words
    
    mov eax, ebx
    imul eax, WORD_SIZE
    lea esi, [words + eax]
    
    push esi
    push fmt_str
    call _printf
    add esp, 8
    
    push newline
    call _printf
    add esp, 4
    
    inc ebx
    jmp .display_loop
    
display_words_done:
    ret

exit_program:
    push goodbye
    call _printf
    add esp, 4

    push 0
    call _exit