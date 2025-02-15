def encrypt_decrypt(text, shift_keys, ifdecrypt):
    """
    Encrypts or decrypts a text using Caesar Cipher with multiple shift keys.

    Args:
        text (str): The text to encrypt or decrypt.
        shift_keys (list): A list of integers representing the shift values for each character.
        ifdecrypt (bool): Flag to determine if decryption (True) or encryption (False) is performed.

    Returns:
        str: The encrypted text if encrypting, or the plain text if decrypting.
    """
    result = []
    shift_keys_len = len(shift_keys)

    for i, char in enumerate(text):
        if 32 <= ord(char) <= 126:  # accepted text chars
            shift = shift_keys[i % shift_keys_len]  # Get the corresponding shift key
            effective_shift = -shift if ifdecrypt else shift  # Reverse shift for decryption

            # Apply the shift and keep within the accepted char range
            shifted_char = chr((ord(char) - 32 + effective_shift) % 94 + 32)
            result.append(shifted_char)

            # Display shifting steps
            print(f"{i} {char} {shift} {shifted_char}")
        else:
            result.append(char)  # for chars outside the accepted range, keep as is

    print("----------")
    return ''.join(result)


# Example usage
if __name__ == "__main__":
    # Input from user
    text = input("").strip()
    shift_keys = list(map(int, input("").strip().split()))

    # Validate constraints
    if len(shift_keys) < 2 or len(shift_keys) > len(text):
        print("Error: Shift keys length must be between 2 and the length of the text.")
    else:
        # Encrypt
        cipher_text = encrypt_decrypt(text, shift_keys, ifdecrypt=False)

        # Decrypt
        decrypted_text = encrypt_decrypt(cipher_text, shift_keys, ifdecrypt=True)

        # Final output
        print(f"Text: {text}")
        print(f"Shift keys: {' '.join(map(str, shift_keys))}")
        print(f"Cipher: {cipher_text}")
        print(f"Decrypted text: {decrypted_text}")
