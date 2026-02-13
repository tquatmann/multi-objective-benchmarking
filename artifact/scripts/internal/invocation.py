from .utility import *
from .execution import Execution

class Invocation(object):

    def __init__(self, invocation_json = None):
        """ Creates either an empty invocation that can be filled using 'add command' or an invocation from an existing json representation."""
        self.commands = []
        self.note = ""
        self.tool = ""
        self.configuration_id = ""
        self.benchmark_id = ""
        self.time_limit = None
        self.run_id = 1
        if invocation_json != None:
            self.benchmark_id = invocation_json["benchmark-id"]
            self.configuration_id = invocation_json["configuration-id"]
            self.tool = invocation_json["tool"]
            self.note = invocation_json["invocation-note"]
            self.time_limit = invocation_json["time-limit"]
            self.run_id = invocation_json["run-id"]
            for c in invocation_json["commands"]:
                self.add_command(c)
            if len(self.commands) == 0:
                raise AssertionError("No command defined for the given invocation")

    def get_identifier_no_run_id(self):
        if "." in self.tool: raise AssertionError("Tool name '{}' contains a '.'. This is problematic as we want to infer the tool name from the logfile name.")
        if "." in self.configuration_id: raise AssertionError("Configuration id '{}' contains a '.'. This is problematic as we want to infer the configuration id from the logfile name.")
        return self.tool + "." + self.configuration_id + "." + self.benchmark_id


    def get_identifier(self):
        if "." in self.tool: raise AssertionError("Tool name '{}' contains a '.'. This is problematic as we want to infer the tool name from the logfile name.")
        if "." in self.configuration_id: raise AssertionError("Configuration id '{}' contains a '.'. This is problematic as we want to infer the configuration id from the logfile name.")
        return self.get_identifier_no_run_id() + ".run" + str(self.run_id)
        
    def add_command(self, command):
        if not isinstance(command, str):
            raise AssertionError("The given command is not a string!")
        self.commands.append(command)

    def to_json(self):
        return OrderedDict([("benchmark-id", self.benchmark_id), ("tool", self.tool), ("configuration-id", self.configuration_id), ("invocation-note", self.note), ("commands", self.commands), ("time-limit", self.time_limit), ("run-id", self.run_id)])

    def execute(self):
        execution = Execution(self)
        execution.run(False) # with warm-up run!
        return execution


