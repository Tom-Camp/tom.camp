package main

import (
	"html/template"
	"log"
	"net/http"

	"github.com/gorilla/mux"
	"github.com/tom-camp/tom.camp/app/system/users"
)

var tpl *template.Template

func init() {
	tpl = template.Must(template.ParseGlob("app/templates/*"))
}

func main() {
	r := mux.NewRouter()
	// Routes consist of a path and a handler function.
	r.HandleFunc("/", IndexHandler)

	// Bind to a port and pass our router in
	log.Fatal(http.ListenAndServe(":8000", r))
}

// IndexHandler ...
func IndexHandler(w http.ResponseWriter, req *http.Request) {
	c := users.GetCookie(w, req)
	tpl.ExecuteTemplate(w, "index.gohtml", c.Value)
}
