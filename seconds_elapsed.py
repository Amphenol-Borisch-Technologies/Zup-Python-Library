from pathlib import Path
import tempfile
import time

def seconds_elapsed(self) -> float:
        """ Returns the number of seconds since this method was last executed for a specific Serial Port/Zup Address combination.
                Inputs:       None
                Outputs:      seconds_elapsed: float, seconds since this method last executed for Zup instance's Serial Port/Zup Address combination.
                Nuances:
                    - User specific; each Windows User has a personal ComX_AddressY_Zup_Seconds_Elapsed.tmp file in their
                        'C:\\Users\\username\\AppData\\Local\\Temp\\1' temporary file folder.  So this method
                        doesn't check elapsed times across all users, just for currently logged in user.
                    - Deleting a ComX_AddressY_Zup_Seconds_Elapsed.tmp file resets its timer anew, so cleaning up 
                        Window's Temporary Files restarts the timer for that specific Windows user.
        """
        f = Path(tempfile.gettempdir() + r'\{}_{}_Zup_Seconds_Elapsed.tmp'.format(self.serial_port.port, str(self.address)))
        if f.exists():
                seconds_elapsed =  time.time() - f.stat().st_mtime # f.stat().st_mtime is last modified time of file f.
        else:
                seconds_elapsed = float('inf')
        f.touch() # Creates file f if non-existent, and sets last modified time of f to now, resetting seconds_elapsed to 0.
        return seconds_elapsed

def test_seconds_elapsed(zup: Zup) -> None:
       assert Path(tempfile.gettempdir()).exists()
       assert type(zup.seconds_elapsed()) == float
       f = Path(tempfile.gettempdir() + r'\{}_{}_Zup_Seconds_Elapsed.tmp'.format(zup.serial_port.port, str(zup.address)))
       assert f.exists()
       assert (time.time() - f.stat().st_mtime) <= 0.1
       # Likely < 0.001, but it's non-deterministic so add (huge) safety margin.
       return None