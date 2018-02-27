import readline


class TabCompleter(object):
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")

    def __init__(self, list_p):
        self.create_list_completer(self, list_p)

    @staticmethod
    def create_list_completer(self, ll):
        def list_completer(text, state):
            line = readline.get_line_buffer()
            if not line:
                return [c + " " for c in ll][state]
            else:

                # return [c.lower() + " " for c in ll if (c.lower()).startswith(line)][state]
                return [c + " " for c in ll if (c.lower()).startswith(line.lower())][state]
        readline.set_completer(list_completer)

'''
if __name__ == "__main__":
    li = ["ab", "aa", "bcd a", "bdf c", "bda b", "bdf d"]
    t = TabCompleter(li)
    ans = input("Complete from list ")
    print(ans)
'''
