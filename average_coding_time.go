package main

import (
	"errors"
	"fmt"
	"os"

	"encoding/json"
	"io/ioutil"
	"net/http"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("average_coding_time")
var format = logging.MustStringFormatter(
	`%{color}%{time:15:04:05.000} %{shortfunc} ▶ %{level:.4s} %{id:03x}%{color:reset} %{message}`,
)

type JIRAClient struct {
	project string
}

func NewJIRAClient(project string) (client *JIRAClient, err error) {
	// XXX Validate project
	err = nil
	client = &JIRAClient{project}
	return client, err
}

func (client *JIRAClient) location(tail string) string {
	return fmt.Sprintf("https://%s.atlassian.net/rest/api/2/%s", client.project, tail)
}

type JIRAUser struct {
	username string
}

func (client *JIRAClient) simpleGet(tail string) (body []byte, err error) {
	// XXX Pagination
	url := client.location(tail)
	response, err := http.Get(url)
	if err != nil {
		return
	}
	log.Debugf("%s response code %d", url, response.StatusCode)
	body, err = ioutil.ReadAll(response.Body)
	if err != nil {
		return
	}
	log.Debugf("%s response body:\n%s", url, body)

	if response.StatusCode != 200 {
		return nil, errors.New("unexpected response")
	}
	return
}

// XXX Maybe you can't list users.
func (client *JIRAClient) Users() (users []JIRAUser, err error) {
	bodyData, err := client.simpleGet("user/search?username=exarkun&orderBy=name")
	if err != nil {
		return
	}
	users = make([]JIRAUser, 5)
	err = json.Unmarshal(bodyData, &users)
	if err != nil {
		return
	}
	s, _ := json.Marshal(users[0])
	fmt.Printf("%s\n", s)
	return
}

type JIRAIssue struct {
	key string
}

func (client *JIRAClient) Issues() (issues []JIRAIssue, err error) {
	bodyData, err := client.simpleGet("search?jql=project=FLOC&orderBy=key")
	if err != nil {
		return nil, err
	}
	issues = make([]JIRAIssue, 5)
	err = json.Unmarshal(bodyData, &issues)
	if err != nil {
		return
	}
	s, _ := json.Marshal(issues[0])
	fmt.Printf("%s\n", s)
	return
}

func fatal(err error) {
	log.Critical(err)
	os.Exit(1)
}

func main() {
	client, error := NewJIRAClient("clusterhq")
	if error != nil {
		fatal(error)
	}
	issues, error := client.Issues()
	if error != nil {
		fatal(error)
	}
	for _, issue := range issues {
		fmt.Printf("issue: %s\n", issue.key)
	}
}
