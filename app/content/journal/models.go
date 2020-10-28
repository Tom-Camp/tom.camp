package journal

import (
	"errors"
	"net/http"

	"github.com/tom-camp/tom.camp/app/system/config"

	"github.com/globalsign/mgo/bson"
)

// Journal ...
type Journal struct {
	// add ID and tags if you need them
	ID       string // `json:"id" bson:"id"`
	Title    string // `json:"title" bson:"title"`
	Body     string // `json:"body" bson:"body"`
	Location string // `json:"location" bson:"location"`
}

// AllJournals ...
func AllJournals() ([]Journal, error) {
	bks := []Journal{}
	err := config.Journals.Find(bson.M{}).All(&bks)
	if err != nil {
		return nil, err
	}
	return bks, nil
}

// OneJournal ...
func OneJournal(r *http.Request) (Journal, error) {
	jrl := Journal{}
	id := r.FormValue("id")
	if id == "" {
		return jrl, errors.New("400. Bad Request")
	}
	err := config.Journals.Find(bson.M{"id": id}).One(&jrl)
	if err != nil {
		return jrl, err
	}
	return jrl, nil
}

// PutJournal ...
func PutJournal(r *http.Request) (Journal, error) {
	// get form values
	jrl := Journal{}
	jrl.ID = r.FormValue("id")
	jrl.Title = r.FormValue("title")
	jrl.Body = r.FormValue("body")
	jrl.Location = r.FormValue("location")

	// validate form values
	if jrl.ID == "" || jrl.Title == "" || jrl.Body == "" {
		return jrl, errors.New("400. Bad request. All fields must be complete")
	}

	// insert values
	err := config.Journals.Insert(jrl)
	if err != nil {
		return jrl, errors.New("500. Internal Server Error." + err.Error())
	}
	return jrl, nil
}

// UpdateJournal ...
func UpdateJournal(r *http.Request) (Journal, error) {
	// get form values
	jrl := Journal{}
	jrl.ID = r.FormValue("id")
	jrl.Title = r.FormValue("title")
	jrl.Body = r.FormValue("body")
	jrl.Location = r.FormValue("location")

	if jrl.ID == "" || jrl.Title == "" || jrl.Body == "" {
		return jrl, errors.New("400: Bad Request. Fields can't be empty")
	}

	// update values
	err := config.Journals.Update(bson.M{"id": jrl.ID}, &jrl)
	if err != nil {
		return jrl, err
	}
	return jrl, nil
}

// DeleteJournal ...
func DeleteJournal(r *http.Request) error {
	id := r.FormValue("id")
	if id == "" {
		return errors.New("400. Bad Request")
	}

	err := config.Journals.Remove(bson.M{"id": id})
	if err != nil {
		return errors.New("500. Internal Server Error")
	}
	return nil
}
