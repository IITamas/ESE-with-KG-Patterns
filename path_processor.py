import ast

class PathProcessor:
    def __init__(self, min_or_num=3, max_or_num=5):
        self.min_or_num = min_or_num
        self.max_or_num = max_or_num
        
    def get_variable_path(self, path, entities):
        """Convert entity paths to query variable paths"""
        variable_path = []
        for entity1, edge, entity2 in path[:-1]:
            if str(entity1) not in entities:
                entities[str(entity1)] = "?e"+str(len(entities))
            if str(entity2) not in entities:
                entities[str(entity2)] = "?e"+str(len(entities))
            variable_path.append((entities[str(entity1)], edge, entities[str(entity2)]))
        if str(path[-1][0]) in entities:
            return variable_path + [(entities[str(path[-1][0])], path[-1][1], path[-1][2])]
        return variable_path + [(path[-1][0], path[-1][1],entities[str(path[-1][2])])]

    def get_variable_paths(self, paths, start_entities):
        """Convert all paths to use variables"""
        entities = {str(start_entities):"?e"}
        variable_paths = []
        for path in paths:
            variable_paths += [self.get_variable_path(path, entities)]
        return variable_paths

    def get_optimal_prefix_from_number(self, number):
        """Generate compact prefix codes"""
        res = chr(ord('a')+number%26)
        number = number // 26
        while(number!=0):
            res = chr(ord('a')+number%26)+res
            number = number // 26
        return res+":"

    def get_prefix(self, url):
        """Extract the namespace prefix from a URL"""
        return "/".join(url.split("/")[:-1])+ ("/"+url.split("/")[-1].split("#")[0]+"#" if "#" in url.split("/")[-1] else "") if "http" in url else ""

    def get_optimal_prefixes_from_path(self, paths):
        """Generate optimal prefixes for all URLs in the paths"""
        prefixes = {'':''}
        for path in paths:
            for entities1, edge, entities2 in path:
                urls = []
                if type(entities1) is not str:
                    urls += entities1
                if type(entities2) is not str:
                    urls += entities2
                urls += [edge]
                for url in urls:
                    prefix = self.get_prefix(url)
                    if prefix not in prefixes:
                        prefixes[prefix] = self.get_optimal_prefix_from_number(len(prefixes))
        return prefixes

    def get_prefixed_url(self, prefix, url):
        """Format URL with prefix or as full URI when needed"""
        no_special = True
        try:
            url.split("#")[-1].split("/")[-1].encode('latin1')
        except UnicodeEncodeError:
            no_special = False
        if no_special and not any([c in url for c in ["(", "+", ")", ",", "'"]]):
            return prefix+url.split("#")[-1].split("/")[-1]
        return "<"+url+">"

    def transform_path_with_prefixes(self, paths, prefixes):
        """Apply prefixes to all paths"""
        new_paths = []
        for path in paths:
            for entities1, edge, entities2 in path:
                if type(entities1) is not str:
                    e1 = [self.get_prefixed_url(prefixes[self.get_prefix(url)],url) for url in entities1]
                    e1.sort()
                else:
                    e1 = entities1
                if type(entities2) is not str:
                    e2 = [self.get_prefixed_url(prefixes[self.get_prefix(url)],url) for url in entities2]
                    e2.sort()
                else:
                    e2 = entities2
                new_paths.append([(e1,self.get_prefixed_url(prefixes[self.get_prefix(edge)],edge), e2)])
        return new_paths
