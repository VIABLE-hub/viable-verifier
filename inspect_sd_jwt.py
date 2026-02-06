import sys
import pkgutil
import importlib
import os
import inspect

def inspect_package(package_name):
    print(f"--- Inspecting {package_name} ---")
    try:
        package = importlib.import_module(package_name)
        print(f"Successfully imported {package_name}")
        
        if hasattr(package, "__version__"):
             print(f"Version: {package.__version__}")
        else:
             print("Version: unknown")
             
        if hasattr(package, "__file__"):
            print(f"Location: {package.__file__}")
            pkg_path = os.path.dirname(package.__file__)
        else:
            print("Location: unknown (namespace signature?)")
            if hasattr(package, "__path__"):
                pkg_path = list(package.__path__)[0]
            else:
                pkg_path = None

        print(f"Top-level Attributes: {dir(package)}")
        
        print(f"\nScanning submodules in {pkg_path}...")
        
        found_sdobj = False
        
        # Recursive walk
        if pkg_path:
            for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, prefix=package_name + "."):
                try:
                    module = importlib.import_module(module_name)
                    # Check for SDObj
                    if "SDObj" in dir(module):
                        print(f"!!! FOUND SDObj in module: {module_name} !!!")
                        found_sdobj = True
                    
                    # Check source code if available for "class SDObj" (in case it's not in __all__)
                    if hasattr(module, "__file__") and module.__file__ and module.__file__.endswith(".py"):
                        try:
                            with open(module.__file__, 'r') as f:
                                content = f.read()
                                if "class SDObj" in content:
                                    print(f"!!! FOUND 'class SDObj' definition in {module.__file__} (might not be exported) !!!")
                        except:
                            pass
                            
                except Exception as e:
                    print(f"  Error importing {module_name}: {e}")
        
        if not found_sdobj:
            print("\nWARNING: SDObj was not found in any reachable submodule.")
            print("It might have been removed or renamed in this version.")

    except ImportError:
        print(f"CRITICAL: Could not import {package_name}. It is likely not installed correctly.")
        print(f"Current sys.path: {sys.path}")

if __name__ == "__main__":
    inspect_package("sd_jwt")
