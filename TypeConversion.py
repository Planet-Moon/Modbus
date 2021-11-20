from math import floor
import copy

def list_to_number(number, length=2, signed=False): #little endian
    """Convert list of integers to a single integer

    Args:
        number (list): List to be converted
        length (int, optional): Wordlength of the list. Defaults to 2.
        signed (bool, optional): True if data should be signed. Defaults to False.

    Returns:
        int: Converted list to a single integer
    """
    unsigned_number = 0
    number_length = len(number)-1
    for i in range(number_length, -1, -1):
        factor = pow(2,16*(number_length-i))
        unsigned_number += number[i] * factor
        pass
    if not signed:
        return unsigned_number
    else:
        mask = 1 << 15 + number_length * 16
        if unsigned_number & mask:
            # negative
            signed_Number = (unsigned_number & ~mask) - mask
        else:
            # positive
            signed_Number = unsigned_number & ~mask
        return signed_Number

def number_to_wordList(number, signed=False, size=1):
    """Convert list to a wordlist. Splits a integer into multiple 16-bit integers.

    Args:
        number (int): Large integer to be converted
        signed (bool, optional): True if data should be signed. Defaults to False.
        size (int, optional): Length of the output list. Defaults to 1.

    Returns:
        list: List of 16-bit integers representing the input number
    """
    numberInternal = copy.copy(number)
    if numberInternal == 0:
        return [0]*size
    returnList = []
    zwei_hoch_16 = (2**16)
    while numberInternal:
        appendValue = round(numberInternal % zwei_hoch_16)
        returnList.append(appendValue)
        numberInternal = int(numberInternal / zwei_hoch_16)
        pass
    returnList = list(reversed(returnList))
    return returnList

def main():
    testList = [32768, 240]
    print("testList:"+str(testList))
    testNumber = list_to_number(testList, signed=True)
    print("testNumber:"+str(testNumber))
    testNumber = 4295163912
    testList = number_to_wordList(testNumber, signed=True, size=len(testList))
    print("testList:"+str(testList))
    zero_check = number_to_wordList(0, signed=True, size=5)
    print("zero_check:"+str(zero_check))

    negative_number = -2560
    negative_test = number_to_wordList(negative_number, signed=True, size=1)
    print("negative_test:"+str(negative_test))
    negative_test_res = list_to_number(negative_test, signed=True)
    print("negative_test_res:"+str(negative_test_res))
    if(negative_number == negative_test_res):
        print("\tzero test Ok")
    else:
        print("\tzero test failed")
    pass


if __name__ == "__main__":
    main()