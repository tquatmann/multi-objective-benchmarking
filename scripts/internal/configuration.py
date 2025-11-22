from collections import OrderedDict

class Configuration(object):

    def __init__(self, configuration_json = None, id = None, note= None, command = None):
        """ Creates either an empty configuration or a configuration from an existing json representation."""
        self.command = command
        self.note = note
        self.identifier = id
        if configuration_json != None:
            self.command = configuration_json["command"]
            if "." in configuration_json["configuration-id"]:
                raise AssertionError("Character '.' is not allowed in configuration identifier {}".format(configuration_json["configuration-id"]))
            self.identifier = configuration_json["configuration-id"]
            self.note = configuration_json["configuration-note"]
 
    def to_json(self):
        return OrderedDict([("configuration-id", self.identifier), ("configuration-note", self.note), ("command", self.command)])


