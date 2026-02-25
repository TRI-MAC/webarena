const core = require('@actions/core');
const github = require('@actions/github');
const yaml = require("js-yaml");
const fs = require("fs");

//JavaScript variant of the sanitize_name function from cdk/cdk/utils.py
function sanitize_name(unsanitized_name){

    const symbol_removal = /[^0-9a-zA-Z-_]+/
    const underscore_replacement = /_+/
    const consecutive_hyphen_removal = /-{2,}/
    const max_length = 40

    let sanitizing_name = unsanitized_name.replace(symbol_removal,"")

    sanitizing_name = sanitizing_name.replace(underscore_replacement,"-")
    sanitizing_name = sanitizing_name.replace(consecutive_hyphen_removal,"-").toLowerCase()

    if (sanitizing_name.length > max_length){
        sanitizing_name = sanitizing_name.substring(0,max_length)
    }

    return sanitizing_name
}

function prepareKeyOrValue(item, modification_type) {
    if (typeof(item) == "string") {
        if (modification_type == "upper") {
            return item.toUpperCase()
        }

        if (modification_type == "lower") {
            return item.toLowerCase()
        }

        if (modification_type == "sanitize"){
            return sanitize_name(item)
        }
    }

    if (Array.isArray(item)) {
        if (modification_type == "upper") {
            return item.map(elem => elem.toUpperCase())
        }

        if (modification_type == "lower") {
            return item.map(elem => elem.toUpperCase())
        }

        if (modification_type == "sanitize"){
            return item.map(elem => sanitize_name(elem))
        }
    }

    return item
}

function recurseGetValues(keyPath, item, object, max_depth, cur_depth = 0, keyModification = null, valueModification = null) {
    if (!object) {
        return 
    }
    if (typeof(item) == "string" || typeof(item) == "int" || typeof(item) == "number") {
        keyString = keyPath.join(".")
        keyString = prepareKeyOrValue(keyString, keyModification)
        value = prepareKeyOrValue(item, valueModification)

        object[keyString] = value
        return 
    }

    if (max_depth == cur_depth) {
        // We have reached our max depth, so we get the keys for that depth and store them in the key_path
        keyString = keyPath.join(".")
        keyString = prepareKeyOrValue(keyString, keyModification)
        object[keyString] = Object.keys(item).map(cur_element => prepareKeyOrValue(cur_element, valueModification))
        return
    }
    
    for (key in item) {
        newKeyPath = keyPath.map(element => element)
        newKeyPath.push(key)
        recurseGetValues(newKeyPath, item[key], object, max_depth, cur_depth + 1, keyModification, valueModification)
    }
    return
}


async function main() {
    try {
        const filePath = core.getInput('file_path');
        // const filePath = "../../../config/development.yaml"

        // Doc is fixed
        const doc = yaml.load(fs.readFileSync(filePath, 'utf8'));

        // Prefix is also fixed
        const prefix = core.getInput("prefix");
        // const prefix = ""

        // Depth of search
        let max_depth = core.getInput("max_depth");
        if (!max_depth) {
            max_depth = -1  
        }
        // const max_depth = null

        let keysToLoad = core.getInput("keys_to_load");
        // let keysToLoad = "github_actions, app_services"
        // let keysToLoad = "github_actions, app_name, env, aws"
        // let keysToLoad = ""

        let keyModification = core.getInput("key_modification");
        // let keyModification = "lower"
        let valueModification = core.getInput("value_modification");
        // let valueModification = "lower"

        if (!keysToLoad) {
            console.log("Loading everything")
            keysToLoad = Object.keys(doc)
        } else {
            keysToLoad = keysToLoad.split(",")
        }

        returnedObject = {}

        console.log(filePath)
        console.log(keysToLoad)
        console.log(prefix)
        console.log(max_depth)

        
        for (var key_index = 0, length = keysToLoad.length; key_index < length; key_index++) {
            key = keysToLoad[key_index].trim()
            console.log("-----")
            console.log(key)
            if (!keysToLoad in doc) {
                console.log("not in document")

            } else {
                initialKeyPath = []
                if (prefix) {
                    initialKeyPath.push(prefix)
                }
                initialKeyPath.push(key)
                recurseGetValues(initialKeyPath, doc[key], returnedObject, max_depth, 0, keyModification, valueModification)
            }
            console.log(returnedObject)
        }
        console.log(returnedObject)
        Object.entries(returnedObject).forEach(([key,value]) => {
            core.setOutput(key, value)
        })
    } catch (error) {
        core.setFailed(error.message);
    }
}

main()