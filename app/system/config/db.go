package config

import (
	"fmt"

	"github.com/globalsign/mgo"
	// Used only with mgo.
	_ "github.com/lib/pq"
)

// DB mongodb database.
var DB *mgo.Database

// Journals is a collections
var Journals *mgo.Collection

func init() {
	// get a mongo sessions
	s, err := mgo.Dial("mongodb://localhost/tmc")
	if err != nil {
		panic(err)
	}

	if err = s.Ping(); err != nil {
		panic(err)
	}

	DB = s.DB("tomcamp")
	Journals = DB.C("journals")

	fmt.Println("You connected to your mongo database.")
}
