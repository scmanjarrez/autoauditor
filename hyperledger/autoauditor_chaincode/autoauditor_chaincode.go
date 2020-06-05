package main

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-protos-go/peer"
)

type SimpleChaincode struct {
}

var pubcol string = "colAaRep"
var privcol string = "colAaRepPriv"

type report struct {
	ObjectType   string `json:"docType"`
	Id           string `json:"id"`
	Organization string `json:"org"`
	Date         string `json:"date"`
	TotalVuln    int    `json:"nvuln"`
	AuditReport  string `json:"report"`
}

func main() {
	err := shim.Start(new(SimpleChaincode))
	if err != nil {
		fmt.Printf("Error starting Simple chaincode: %s", err)
	}
}

func (t *SimpleChaincode) Init(stub shim.ChaincodeStubInterface) peer.Response {
	return shim.Success(nil)
}

func (t *SimpleChaincode) Invoke(stub shim.ChaincodeStubInterface) peer.Response {
	function, args := stub.GetFunctionAndParameters()

	switch function {
	case "new":
		return t.newReport(stub, args)
	case "delete":
		return t.deleteReport(stub, args)
	case "searchReport":
		return t.getById(stub, args)
	// case "searchByDate":
	// 	//find reports by date
	// 	return t.getByDate(stub, args)
	// case "searchByDateRange":
	// 	//find reports by date range
	// 	return t.getByDateRange(stub, args)
	// case "searchByOrganization":
	// 	//find reports by organization
	// 	return t.getByOrganization(stub, args)
	default:
		return shim.Error("Invoke funtion not found. Choose between new, delete or searchReport.")
	}
}

func (t *SimpleChaincode) newReport(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	var err error

	if len(args) != 0 {
		return shim.Error("Incorrect number of arguments. Private report data must be passed in transient map.")
	}

	transMap, err := stub.GetTransient()
	if err != nil {
		return shim.Error("Error getting transient: " + err.Error())
	}

	reportJsonBytes, ok := transMap["aareport"]
	if !ok {
		return shim.Error("aareport must be a key in the transient map")
	}

	if len(reportJsonBytes) == 0 {
		return shim.Error("aareport value in the transient map must be a non-empty JSON string")
	}

	type reportTransientInput struct {
		Id           string `json:"id"`
		Organization string `json:"org"`
		Date         string `json:"date"`
		NVuln        int    `json:"nvuln"`
		Private      bool   `json:"private"`
		Report       string `json:"report"`
	}

	var reportInput reportTransientInput
	err = json.Unmarshal(reportJsonBytes, &reportInput)
	if err != nil {
		return shim.Error("Failed to decode JSON of: " + string(reportJsonBytes))
	}

	if len(reportInput.Id) == 0 {
		return shim.Error("id field must be a non-empty string.")
	}

	if len(reportInput.Organization) == 0 {
		return shim.Error("org field must be a non-empty string.")
	}

	if len(reportInput.Date) == 0 {
		return shim.Error("date field must be a non-empty string.")
	}

	if reportInput.NVuln <= 0 {
		return shim.Error("nvuln field must be a positive integer.")
	}

	if len(reportInput.Report) == 0 {
		return shim.Error("report field must be a non-empty string.")
	}

	var collect string

	if reportInput.Private {
		collect = privcol
	} else {
		collect = pubcol
	}

	objT := "AutoauditorReport"

	reportId := reportInput.Id

	reportAsBytes, err := stub.GetPrivateData(collect, reportId)
	if err != nil {
		return shim.Error("Failed to get report " + reportId + ": " + err.Error())
	} else if reportAsBytes != nil {
		return shim.Error("Report already exists: " + reportId)
	}

	report := &report{
		ObjectType:   objT,
		Id:           reportInput.Id,
		Organization: reportInput.Organization,
		Date:         reportInput.Date,
		TotalVuln:    reportInput.NVuln,
		AuditReport:  reportInput.Report,
	}

	reportJSONasBytes, err := json.Marshal(report)
	if err != nil {
		return shim.Error(err.Error())
	}

	err = stub.PutPrivateData(collect, reportInput.Id, reportJSONasBytes)
	if err != nil {
		return shim.Error(err.Error())
	}

	return shim.Success(nil)
}

func (t *SimpleChaincode) getById(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	var id string
	var valAsbytes []byte
	var err error

	if len(args) < 1 || len(args) > 2 {
		return shim.Error("Incorrect number of arguments. Expecting id of the report to query. Optionally, database can be passed: public or private.")
	}

	id = args[0]

	if len(args) == 1 {
		valAsbytes, err = stub.GetPrivateData(privcol, id) // try private report
		if err != nil || valAsbytes == nil {
			valAsbytes, err = stub.GetPrivateData(pubcol, id) // try simple report
			if err != nil {
				return shim.Error("Failed to get report " + id + ": " + err.Error())
			} else if valAsbytes == nil {
				return shim.Error("Report does not exist: " + id)
			}
		}
	} else {
		col := args[1]
		var collect string
		switch col {
		case "private":
			collect = privcol
		case "public":
			collect = pubcol
		default:
			return shim.Error("Collection does not exist: " + col + ". Choose between public or private")
		}

		valAsbytes, err = stub.GetPrivateData(collect, id)
		if err != nil {
			return shim.Error("Failed to get report " + id + ": " + err.Error())
		} else if valAsbytes == nil {
			return shim.Error("Report does not exist: " + id)
		}
	}

	return shim.Success(valAsbytes)
}

func (t *SimpleChaincode) deleteReport(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	type reportDeleteTransientInput struct {
		Id string `json:"id"`
	}

	if len(args) != 0 {
		return shim.Error("Incorrect number of arguments. Report id must be passed in transient map.")
	}

	transMap, err := stub.GetTransient()
	if err != nil {
		return shim.Error("Error getting transient: " + err.Error())
	}

	reportDeleteJsonBytes, ok := transMap["aareport_delete"]
	if !ok {
		return shim.Error("aareport_delete must be a key in the transient map.")
	}

	if len(reportDeleteJsonBytes) == 0 {
		return shim.Error("aareport_delete value in the transient map must be a non-empty JSON string.")
	}

	var reportDeleteInput reportDeleteTransientInput
	err = json.Unmarshal(reportDeleteJsonBytes, &reportDeleteInput)
	if err != nil {
		return shim.Error("Failed to decode JSON: " + string(reportDeleteJsonBytes))
	}

	if len(reportDeleteInput.Id) == 0 {
		return shim.Error("id field must be a non-empty string.")
	}

	err = stub.DelPrivateData(pubcol, reportDeleteInput.Id)
	if err != nil {
		return shim.Error(err.Error())
	}

	err = stub.DelPrivateData(privcol, reportDeleteInput.Id)
	if err != nil {
		return shim.Error(err.Error())
	}

	return shim.Success(nil)
}
