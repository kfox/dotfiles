#!/usr/bin/osascript

try
	tell application "Viscosity"
		if the state of the first connection is not "Connected" then
			connect the first connection
			
			repeat until state of the first connection is "Connected"
				delay 1
			end repeat
		end if
	end tell
on error
	tell me to quit
end try

