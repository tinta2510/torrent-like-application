import uvicorn

def main():
    print("Hello")
    uvicorn.run("torrent_tracker.tracker:app", reload=True)

if __name__ == "__main__":
    main()