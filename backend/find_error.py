
try:
    print("Importing src...")
    import src
    print("Importing src.__init__...")
    from src import create_app
    print("Calling create_app()...")
    app = create_app()
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
