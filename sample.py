def find_duplicates(items):
    result = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j] and items[i] not in result:
                result.append(items[i])
    return result
