# Palimpsest

Imagine you have riced your _almighty Arch_ install (or wathever) to the extreme, but suddenly you want to change the color scheme...
You need to edit the configuration of multiple softwares, this may include:

* Window Manager (colors, font...)
* Terminal emulator (mainly font)
* Shell (colors)
* Editor (vim colors)
* GUI Toolkit (GTK theme, qt theme...)

This is a heavy burden for someone who likes to change his color scheme regularly...

## What is it?

Palimpsest is a tool meant to synchronize two directories (`src` and `out`). The key feature is that it allows you to apply some kind of processing to the source files.

The processing essentially replaces instances of `@{some.key}` with its corresponding value in a resource file. The resource file is JSON, you can put wahtever you want in it.

This means that a file `src/hillbilly.lua` having following content:

	theme = {}
	theme.font = "@{theme.font}"

	theme.color = {}
	theme.color.gray       = "@{theme.colors.gray}"
	theme.color.arc_darker = "@{theme.colors.darker}"
	theme.color.arc_dark   = "@{theme.colors.dark}"
	...

will be processed and output to `out/hillbilly.lua`:

	theme = {}
	theme.font = "dina 8"

	theme.color = {}
	theme.color.gray       = "#858c98"
	theme.color.arc_darker = "#2f343f"
	theme.color.arc_dark   = "#3e424d"
	...

## How to use it?

`palimpsest --src-dir path/to/src --out-dir path/to/out --resources-file path/to/resources.json`

You can also enable daemonized mode with `--daemon`. This will continuously watch for changes and update your `out` directory accordingly.

For more options:

`palimpsest -h`

You can save all your command line options in a JSON file and pass it with --config-file.

An example configuration and resources file is included.

## Copying

This software is licensed under GNU General Public License. See `COPYING` for more informations.
