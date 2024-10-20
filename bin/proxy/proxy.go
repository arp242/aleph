package main

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"mime"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

var c = &http.Client{
	Timeout: 10 * time.Second,
}

var index []byte

type file struct {
	t string
	d []byte
}

var (
	files   = make(map[string]file)
	filesMu sync.Mutex
)

func handle(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	path := r.URL.String()

	// Proxy to API
	if strings.HasPrefix(path, "/api/") {
		fmt.Printf("%-5s  %s\n", "api", path)

		req, err := http.NewRequest(r.Method, "http://localhost:8000"+path, r.Body)
		if err != nil {
			fmt.Println(err)
			http.Error(w, err.Error(), 500)
			return
		}

		resp, err := c.Do(req)
		if err != nil {
			fmt.Println(err)
			http.Error(w, err.Error(), 500)
			return
		}
		defer resp.Body.Close()

		for k, v := range resp.Header {
			w.Header()[k] = v
		}
		w.WriteHeader(resp.StatusCode)

		_, err = io.Copy(w, resp.Body)
		if err != nil {
			fmt.Println(err)
		}
		return
	}

	// Non-static files are JS permalinks.
	if !strings.HasPrefix(path, "/static") {
		fmt.Printf("%-5s  %s\n", "index", path)
		w.Write(index)
		return
	}

	// Load from FS.
	fmt.Printf("%-5s  %s\n", "fs", path)
	filesMu.Lock()
	if f, ok := files[path]; ok {
		filesMu.Unlock()
		w.Header().Set("Content-Type", f.t)
		w.Write(f.d)
		return
	}
	filesMu.Unlock()
	fp, err := os.Open("." + path)
	if err != nil {
		code, msg := 400, err.Error()
		if errors.Is(err, fs.ErrNotExist) {
			code, msg = 404, "not found: "+path
		}
		http.Error(w, msg, code)
		return
	}
	defer fp.Close()
	d, err := io.ReadAll(fp)
	if err != nil {
		fmt.Println(err)
		return
	}

	f := file{d: d, t: mime.TypeByExtension(filepath.Ext(path))}

	w.Header().Set("Content-Type", f.t)
	w.Write(f.d)

	filesMu.Lock()
	files[path] = f
	filesMu.Unlock()
}

func main() {
	if len(os.Args) > 1 {
		err := os.Chdir(os.Args[1])
		if err != nil {
			panic(err)
		}
	}

	d, err := os.ReadFile("index.html")
	if err != nil {
		panic(err)
	}
	index = bytes.ReplaceAll(d,
		[]byte(`data-api-endpoint="/api/2/"`),
		[]byte(`data-api-endpoint="http://aleph.localhost:8000/api/2/"`))

	err = http.ListenAndServe("127.0.0.1:8080", http.HandlerFunc(handle))
	if err != nil {
		panic(err)
	}
}
