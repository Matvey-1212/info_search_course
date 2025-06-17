class CastomCounter:
    def __init__(self, input_list=None):
        self.size = 100007 
        self.buckets = [[] for _ in range(self.size)]
        self.load_factor_threshold = 0.75
        self.count = 0
        
        if input_list is not None:
            for key in input_list:
                self.put(key)

    def hash(self, key):
        s = str(key)
        h = 0
        for c in s:
            h = (h * 31 + ord(c)) % self.size
        return h

    def put(self, key, value=None):
        
        if self.count / self.size >= self.load_factor_threshold:
            self.rehash()
        
        h = self.hash(key)
        for i, (k, v) in enumerate(self.buckets[h]):
            if k == key:
                self.buckets[h][i] = (key, v+1 if value is None else value)
                return
        self.buckets[h].append((key, 1 if value is None else value))
        self.count += 1

    def get(self, key):
        h = self.hash(key)
        for k, v in self.buckets[h]:
            if k == key:
                return v
        return None

    def items(self):
        for bucket in self.buckets:
            for k, v in bucket:
                yield k, v

    def most_common(self, n):
        return sorted(self.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def __len__(self):
        return self.count
    
    def rehash(self):
        old_buckets = self.buckets
        self.size *= 2
        self.buckets = [[] for _ in range(self.size)]
        self.count = 0

        for bucket in old_buckets:
            for key, value in bucket:
                self.put(key, value)
