package users

import (
	uuid "github.com/satori/go.uuid"
	"log"
	"net/http"
)

// GetCookie adds func to get cookie
func GetCookie(w http.ResponseWriter, req *http.Request) *http.Cookie {
	c, err := req.Cookie("session")
	if err != nil {
		sID, err := uuid.NewV4()
		if err != nil {
			log.Println(err)
		}
		c = &http.Cookie{
			Name:  "session",
			Value: sID.String(),
		}
		http.SetCookie(w, c)
	}
	return c
}
