case "$1" in
e)	vi -p .x
	;;
i)	set -x
        [ -e .venv ] || python3 -m venv .venv;
        .venv/bin/python3 -m pip install python-vlc pysrt numpy #pydub
	;;
*)      clear
        .venv/bin/python3 ./main.py
        ;;
esac
