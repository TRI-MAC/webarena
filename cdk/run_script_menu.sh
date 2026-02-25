# Function to display the menu
show_menu() {
    echo "=============================="
    echo "         Main Menu            "
    echo "=============================="
    echo "1. Run run_local.sh"
    echo "2. Run cleanup_local_run.sh"
    echo "3. Exit"
    echo "=============================="
    echo -n "Please enter your choice [1-3]: "
}

# Function to execute the selected script
execute_choice() {
    case $1 in
        1)
            ./scripts/run_local.sh
            ;;
        2)
            ./scripts/cleanup_local_run.sh
            ;;
        3)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice, please select a valid option."
            ;;
    esac
}

# Main loop
while true; do
    show_menu
    read choice
    execute_choice $choice
done


