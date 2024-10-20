Branch with some changes to make it easier to run for Alfred dev.

Use the compose.yaml from Alfred. The services between Alfred and Aleph will be
shared.

It will use the ui from alfred. It's assumed that the alfred checkout is next to
the aleph one – for example:

    ~/code/occrp/aleph
    ~/code/occrp/alfred

Add `./bin` to $PATH; this will add the following commands:

    aleph        – just the Aleph CLI.
    aleph-serve  – serve the Aleph API.
    aleph-proxy  – serve static files, proxy API requests.
    tmux-aleph   – set up tmux session with aleph-serve, aleph-proxy, and aleph worker.

Open at http://aleph.localhost:8080

All of these should deal with venv nonsense and all of that. The upshot of doing
it like this is that adding some debug `print()` and whatnot is quick and easy.
