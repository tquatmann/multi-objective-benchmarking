from .utility import *

def input_storm_binary_dir(settings):
    """ Asks the user to enter a path to the storm binaries."""
    response = input("Enter path to storm binary directory [{}]: ".format(settings.storm_binary_dir()))
    if response != "":
        settings.json_data["storm-binary-dir"] = response
        settings.save()
        
def input_mcsta_binary_dir(settings):
    """ Asks the user to enter a path to the mcsta binaries."""
    response = input("Enter path to mcsta binary directory [{}]: ".format(settings.mcsta_binary_dir()))
    if response != "":
        settings.json_data["mcsta-binary-dir"] = response
        settings.save()

def input_number_of_runs():
    """ Asks the user to enter a number of times the experiment is executed."""
    result = 1
    while True:
        response = input("Enter the number of times each experiment should be repeated [{}]: ".format(result))
        if response == "": break
        if is_number(response) and int(response) > 0:
            result = int(response)
            break
        else:
            print("Number of runs should be a positive integer number.")
    return result

def input_logs_dir(settings):
    """ Asks the user to enter a directory in which the tool logs are stored."""
    response = input("Enter a directory in which the tool logs are stored [{}]: ".format(settings.logs_dir()))
    if response != "":
        settings.json_data["logs-directory-name"] = response
        settings.save()

def input_time_limit(settings):
    """ Asks the user to enter a time limit."""
    while True:
        response = input("Enter a time limit (in seconds) after which executions are aborted [{}]: ".format(settings.time_limit()))
        if response == "": break
        if is_number(response):
            settings.json_data["time-limit"] = int(response)
            settings.save()
            break
        else:
            print("Time limit should be a number.")

def input_selection(item : str, options : OrderedDict, single_choice = False):
    if not single_choice:
        if "a" in options: raise AssertionError("options should not include key 'a'")
        if "d" in options: raise AssertionError("options should not include key 'd'")
        if "c" in options: raise AssertionError("options should not include key 'c'")
    if len(options) == 0: raise AssertionError("options should not be empty.")
    longest_option_descriptions = []
    longest_option_descriptions.append(max([len(key) for key in options] + [4]) + 4)
    i = 0
    while True:
        longest = -1
        for key in options:
            if i < len(options[key]):
                longest = max(longest, len(options[key][i]))
        if longest >= 0:
            longest_option_descriptions.append(longest + 4)
        else:
            break
        i += 1
        
    selected_keys = []      
    while True:
        keys = []
        print("Select {}.".format(item))
        print("    Option" + " " * (longest_option_descriptions[0] - len("Option")) + "Description")
        print("----" + "-" * sum(longest_option_descriptions))
        for key in options:
            keys.append(key)
            description = ""
            for i in range(len(options[key])):
                description += "{}{}".format(options[key][i], " " * (longest_option_descriptions[i+1] - len(options[key][i])))
            print("{}{}{}".format("[X] " if key in selected_keys else "[ ] ", key + " " * (longest_option_descriptions[0] - len(key)), description))
        if not single_choice:
            keys.append("a")
            print("    {}Select all".format("a" + " " * (longest_option_descriptions[0] - 1)))
        if not single_choice and len(selected_keys) > 0:
            keys.append("c")
            print("    {}Clear selection".format("c" + " " * (longest_option_descriptions[0] - 1)))
            keys.append("d")
            print("    {}done".format("d" + " " * (longest_option_descriptions[0] - 1)))
        selection = input("Enter option: ")
        if selection in keys:            
            if selection in options:
                selected_keys.append(selection)
                if single_choice:
                    break
            elif selection == "a":
                selected_keys = keys[:len(options)]
                break
            elif selection == "d":
                break
            elif selection == "c":
                selected_keys = []
        else:
            print ("Invalid selection. Enter any of {} or press Ctrl+C to abort.".format(keys))  
    print("Selected {}: {}".format(item,selected_keys))
    return selected_keys