from collections.abc import MutableSet

class OrderedSet(MutableSet):
    def __init__(self, iterable=None):
        self.elements = []
        self.lookup = set()
        if iterable is not None:
            self |= iterable

    def __contains__(self, value):
        return value in self.lookup

    def __iter__(self):
        return iter(self.elements)

    def __len__(self):
        return len(self.elements)

    def add(self, value):
        if value not in self.lookup:
            self.lookup.add(value)
            self.elements.append(value)

    def discard(self, value):
        if value in self.lookup:
            self.lookup.remove(value)
            self.elements.remove(value)

    def __repr__(self):
        return f"{type(self).__name__}({self.elements})"

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return self.elements == other.elements
        return NotImplemented

    def __getitem__(self, index):
        return self.elements[index]

    def __reversed__(self):
        return reversed(self.elements)