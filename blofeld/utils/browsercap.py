from ConfigParser import SafeConfigParser as ConfigParser
import re
import os



__all__ = [
   "BrowserCapabilities"
]


BC_PATH = os.path.abspath(os.path.dirname(__file__ or os.getcwd()))



class Browser(object):


    def __init__(self, capabilities):
        self.lazy_flag = True
        self.cap = capabilities


    def parse(self):
        for name, value in self.cap.items():
            if name in ["tables", "aol", "javaapplets",
                       "activexcontrols", "backgroundsounds",
                       "vbscript", "win16", "javascript", "cdf",
                       "wap", "crawler", "netclr", "beta",
                        "iframes", "frames", "stripper", "wap"]:
                self.cap[name] = (value.strip().lower() == "true")
            elif name in ["ecmascriptversion", "w3cdomversion"]:
                self.cap[name] = float(value)
            elif name in ["css"]:
                self.cap[name] = int(value)
            else:
                self.cap[name] = value
        self.lazy_flag = False


    def __repr__(self):
        if self.lazy_flag: self.parse()
        return repr(self.cap)


    def get(self, name, default=None):
        if self.lazy_flag: self.parse()
        try:
            return self[name]
        except KeyError:
            return default


    def __getitem__(self, name):
        if self.lazy_flag: self.parse()
        return self.cap[name.lower()]


    def keys(self):
        return self.cap.keys()


    def items(self):
        if self.lazy_flag: self.parse()
        return self.cap.items()


    def values(self):
        if self.lazy_flag: self.parse()
        return self.cap.values()
    

    def __len__(self):
        return len(self.cap)


    def supports(self, feature):
        value = self.cap.get(feature)
        if value == None:
            return False
        return value


    def features(self):
        l = []
        for f in ["tables", "frames", "iframes", "javascript",
                  "cookies", "w3cdomversion", "wap"]:
            if self.supports(f):
                l.append(f)
        if self.supports_java():
            l.append("java")
        if self.supports_activex():
            l.append("activex")
        css = self.css_version()
        if css > 0:
            l.append("css1")
        if css > 1:
            l.append("css2")
        return l


    def supports_tables(self):
        return self.supports("frames")

    def supports_iframes(self):
        return self.supports("iframes")


    def supports_frames(self):
        return self.supports("frames")


    def supports_java(self):
        return self.supports("javaapplets")


    def supports_javascript(self):
        return self.supports("javascript")


    def supports_vbscript(self):
        return self.supports("vbscript")


    def supports_activex(self):
        return self.supports("activexcontrols")


    def supports_cookies(self):
        return self.supports("cookies")


    def supports_wap(self):
        return self.supports("wap")


    def css_version(self):
        return self.get("css", 0)


    def version(self):
        major = self.get("majorver")
        minor = self.get("minorver")
        if major and minor:
            return (major, minor)
        elif major:
            return (major, None)
        elif minor:
            return (None, minor)
        else:
            ver = self.get("version")
            if ver and "." in ver:
                return tuple(ver.split(".", 1))
            elif ver:
                return (ver, None)
            else:
                return (None, None)


    def dom_version(self):
        return self.get("w3cdomversion", 0)


    def is_bot(self):
        return self.get("crawler") == True


    def is_mobile(self):
        return self.get("ismobiledevice") == True

    
    def name(self):
        return self.get("browser")




class BrowserCapabilities(object):


    def __new__(cls, *args, **kwargs):
        # Only create one instance of this clas
        if "instance" not in cls.__dict__:
            cls.instance = object.__new__(cls, *args, **kwargs)
        return cls.instance


    def __init__(self):
        self.cache = {}
        self.parse()


    def parse(self):
        cfg = ConfigParser()
        files = ("browscap.ini", "bupdate.ini")
        read_ok = cfg.read([os.path.join(BC_PATH, name) for name in files])
        if len(read_ok) == 0:
            raise IOError, "Could not read browscap.ini, " + \
                  "please get it from http://www.GaryKeith.com"
        self.sections = []
        self.items = {}
        self.browsers = {}
        parents = set()
        for name in cfg.sections():
            qname = name
            for unsafe in list("^$()[].-"):
                qname = qname.replace(unsafe, "\%s" % unsafe)
            qname = qname.replace("?", ".").replace("*", ".*?")
            qname = "^%s$" % qname
            sec_re = re.compile(qname)
            sec = dict(regex=qname)
            sec.update(cfg.items(name))
            p = sec.get("parent")
            if p: parents.add(p)
            self.browsers[name] = sec
            if name not in parents:
                self.sections.append(sec_re)
            self.items[sec_re] = sec


    def query(self, useragent):
        b = self.cache.get(useragent)
        if b: return b

        for sec_pat in self.sections:
            if sec_pat.match(useragent):
                browser = dict(agent=useragent)
                browser.update(self.items[sec_pat])
                parent = browser.get("parent")
                while parent:
                    items = self.browsers[parent]
                    for key, value in items.items():
                        if key not in browser.keys():
                            browser[key] = value
                        elif key == "browser" and value != "DefaultProperties":
                            browser["category"] = value # Wget, Godzilla -> Download Managers
                    parent = items.get("parent")
                if browser.get("browser") != "Default Browser":
                    b = Browser(browser)
                    self.cache[useragent] = b 
                    return b
        self.cache[useragent] = None


    __call__ = query



def test():
    bc = BrowserCapabilities()
    for agent in [
        "Mozilla/5.0 (compatible; Konqueror/3.5; Linux; X11; de) KHTML/3.5.2 (like Gecko) Kubuntu 6.06 Dapper",
        "Mozilla/5.0 (X11; U; Linux i686; de; rv:1.8.0.5) Gecko/20060731 Ubuntu/dapper-security Firefox/1.5.0.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.12) Gecko/20060216 Debian/1.7.12-1.1ubuntu2",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.5) Gecko/20060731 Ubuntu/dapper-security Epiphany/2.14 Firefox/1.5.0.5",
        "Opera/9.00 (X11; Linux i686; U; en)",
        "Wget/1.10.2",
        "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20051128 Kazehakase/0.3.3 Debian/0.3.3-1",
        "Mozilla/5.0 (X11; U; Linux i386) Gecko/20063102 Galeon/1.3test",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows 98)" # Tested under Wine
      ]:
        b = bc(agent)
        if not b:
            print "!", agent
        else:
            print b.name(), b.version(), b.get("category", ""), b.features()


def update():
    import urllib
    urllib.urlretrieve("http://browsers.garykeith.com/stream.asp?BrowsCapINI",
                       "browscap.ini")


if __name__ == "__main__":
    import sys, os
    bc_filename = os.path.join(BC_PATH, "browscap.ini")
    if not os.path.exists(bc_filename) or "-update" in sys.argv[1:]:
        print "Downloading browser database to %r..." % bc_filename,
        update()
        print "done"
    test()
