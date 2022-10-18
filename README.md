# python-built-tool

## What is it?

This is a build system for Python programs that generates an installer for the platform it is built on.

It uses PyInstaller to bundle the code, resources and python runtime into an executable and a platform dependent program to generate an installer.

It is a fork of FBS by Michael Herrmann with a major refactoring to remove the runtime and Qt dependencies. It is not affiliated with FBS.

## What is FBS?
FBS is a build system for Qt Python applications developed by Michael Herrmann.
https://github.com/mherrmann/fbs
https://build-system.fman.io.

## Why does this exist?

We wanted a build tool that could take an existing executable python package and produce an installer that could be distributed to end users.

PyInstaller does most of the work, but it doesn't actually create an installer (despite its name).

FBS had all the functionality that we wanted but there were a number of things we didn't like about it.
1) It is tied to the Qt GUI platform and we wanted a build tool that is independent of any runtime libraries.
2) It has a very restricting unpythonic project structure that we did not much like.
3) It has a runtime component which means the program cannot be run without FBS. This enforces the GPL on your program if you do not purchase a licence. [Removal of this component removes this requirement](https://www.gnu.org/licenses/gpl-faq.en.html#CanIUseGPLToolsForNF).
4) The version number must be defined in the json settings

## What has changed from FBS?

1) It should now support 3.5+
2) The Qt dependency has been stripped out. This allows it to be used with any GUI library or just a CLI app.
3) The project structure has been refactored. The build files have been moved out of `src` and into `build_tools`. The path is configurable.
4) The runtime resource system has been stripped out. We did not like that resources were stored outside the package. We suggest users implement this with standard packaging tools if they want platform dependent resources.
5) The runtime component has been removed. [This means your code does not depend on a GPL component so it can use any licence you like](https://www.gnu.org/licenses/gpl-faq.en.html#CanIUseGPLToolsForNF).
6) The version number now supports the full PEP 440 specification.
7) The version number can be optionally pulled from your package. `"version": "attr: my_app.__version__"`
8) main_module is defined as the module name not its path. Eg `"main_module": "my_app"`. If the package has been installed, this will allow the built tool to use the installed version instead of the source version.
9) `icons` directory has been moved into `build_system`

## How do I use it?

1) Install any version of Python 3.5+
2) Download the source code from github and extract it to your computer
3) Optionally set up a virtual environment and enable it
4) Run `python -m pip install <path>` replacing `<path>` with the path to the directory extracted in step 2. On linux and mac use `python3` instead
5) Run `pbt startproject` to create a new project. This will prompt you for some inputs and then will create a hello world package, packaging files and build_system directory.
6) You can then run `pbt run` to execute the package. You can also execute the package like you normally would with a python package.
7) Run `pbt freeze` which will call PyInstaller and generate a packaged executable for your application in `target`. Try running it to make sure it works.
8) Run `pbt installer` to create an installer for your application that you can distribute.

More detailed information can be found in the [FBS tutorial](https://github.com/mherrmann/fbs-tutorial)
