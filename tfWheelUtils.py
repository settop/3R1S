#!/usr/bin/python3

class TfCharacter:
    def __init__(self):
        self.name = ""
        self.weight = 1
        self.tags = []
        self.specificUser = None

class TfCharacters:
    def __init__(self):
        self.characters = []

    def GetCharactersAndWeights(self, userID, includeTags, excludeTags):
        characters = []
        cumulativeWeights = []
        totalWeight = 0
        for c in self.characters:
            if c.specificUser is not None and c.specificUser != userID:
                continue
            included = includeTags is None or len(includeTags) == 0
            for tag in c.tags:
                included = included or tag in includeTags
                excluded = excludeTags is not None and tag in excludeTags
                if excluded:
                    included = False
                    break
            if included:
                characters.append(c.name)
                totalWeight += c.weight
                cumulativeWeights.append(totalWeight)
        return characters, cumulativeWeights
