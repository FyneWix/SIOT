import asyncio
from bleak import BleakScanner, BleakClient

# Define a timeout period in seconds.
TIMEOUT = 10

async def get_device_services(address):
    async with BleakClient(address) as client:
        if not client.is_connected:
            print(f"Failed to connect to {address}.")
            return []

        print(f"Connected to {address}. Discovering services...")
        return client.services

async def discover_and_select():
    while True:
        # Step 1: Discover devices.
        print("Scanning for devices...")
        devices = await BleakScanner.discover()

        if not devices:
            print("No devices found.")
            continue

        # Step 2: List devices with index numbers for selection.
        print("Found devices:")
        for i, device in enumerate(devices):
            print(f"{i}. {device.name} ({device.address})")

        # Step 3: Prompt the user to select a device.
        selection = None
        while selection is None:
            user_input = input("Enter the number of the device to scan further: ")
            if user_input.isdigit():
                user_input = int(user_input)
                if 0 <= user_input < len(devices):
                    selection = user_input
                else:
                    print("Invalid selection. Please enter a number within the valid range.")
            else:
                print("Invalid input. Please enter a number.")

        selected_device = devices[selection]
        print(f"Selected device: {selected_device.name} ({selected_device.address})")

        # Step 4: Scan the selected device for services and characteristics.
        try:
            services = await asyncio.wait_for(get_device_services(selected_device.address), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            print(f"Timeout while discovering services on {selected_device.address}. Re-scanning for devices...")
            continue

        if not services:
            print("No services found.")
            continue

        # Step 5: List services and characteristics for user selection.
        print("\nAvailable services and characteristics:")
        service_index = {}
        char_index = {}
        char_count = 0

        for i, service in enumerate(services):
            print(f"{i}. Service: {service.handle} {service.uuid} {service.description}")
            service_index[i] = service
            for char in service.characteristics:
                print(f"  {char_count}. Characteristic: {char.handle} {char.uuid} {char.description} {char.properties}")
                char_index[char_count] = char
                char_count += 1

        # Step 6: Loop to read or write to characteristics, or rescan.
        while True:
            # Prompt user to select a characteristic, or type 'rescan', 'exit', or 'write'.
            user_input = input("Enter the number of the characteristic to read value, 'write' to write value, 'rescan' to rescan, or 'exit' to exit: ")

            if user_input.lower() == 'rescan':
                break  # Exit to rescanning loop.
            elif user_input.lower() == 'exit':
                return  # Exit the entire program.

            if user_input.lower() == 'write':
                # Prompt for characteristic index and value to write.
                char_index_input = input("Enter the number of the characteristic to write to: ")
                if char_index_input.isdigit():
                    char_index_input = int(char_index_input)
                    if 0 <= char_index_input < len(char_index):
                        selected_char = char_index[char_index_input]
                        value_to_write = input(f"Enter the value to write to characteristic {selected_char.uuid}: ")
                        
                        try:
                            # Convert value to bytes if necessary.
                            value_bytes = bytes(value_to_write, 'ascii')
                            async with BleakClient(selected_device.address) as client:
                                if not client.is_connected:
                                    print(f"Failed to connect to {selected_device.address}")
                                    continue

                                print(f"Connected to {selected_device.address}. Writing characteristic value...")
                                response = await client.write_gatt_char(selected_char.uuid, value_bytes, response=True)
                                print(f"Value written to characteristic {selected_char.uuid}. Response: {response}")
                        except Exception as e:
                            print(f"An error occurred while writing to characteristic {selected_char.uuid}: {e}")
                    else:
                        print("Invalid selection. Please enter a number within the valid range.")
                else:
                    print("Invalid input. Please enter a number.")
                continue  # Continue the loop after writing.

            if user_input.isdigit():
                user_input = int(user_input)
                if 0 <= user_input < len(char_index):
                    selected_char = char_index[user_input]
                    print(f"Selected characteristic: {selected_char.handle} {selected_char.uuid}")

                    # Step 7: Read and print the value of the selected characteristic.
                    async with BleakClient(selected_device.address) as client:
                        if not client.is_connected:
                            print(f"Failed to connect to {selected_device.address}")
                            continue

                        print(f"Connected to {selected_device.address}. Reading characteristic value...")
                        try:
                            value = await client.read_gatt_char(selected_char.uuid)
                            print(f"Value of characteristic {selected_char.uuid}: {value}")
                        except Exception as e:
                            print(f"An error occurred while reading characteristic {selected_char.uuid}: {e}")
                else:
                    print("Invalid selection. Please enter a number within the valid range.")
            else:
                print("Invalid input. Please enter a number, 'write', 'rescan', or 'exit'.")

if __name__ == "__main__":
    asyncio.run(discover_and_select())
