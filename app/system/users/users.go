package users

type users struct {
	Mail     string `schema:"mail,required"`
	Password string `schema:"password,required"`
	First    string `schema:"frist"`
	Last     string `schema:"last"`
}
