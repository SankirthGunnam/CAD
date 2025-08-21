class Model:
    def __init__(self, parent, rdb: "RDBManager"):
        self.parent = parent
        self.rdb = rdb
        self.all_devices_model = TableModel(self, [])
        self.selected_devices_model = TableModel(self, [])

    def change_model_data(self):
        current_revision = self.rdb[paths.CURRENT_REVISION]

        if current_revision and paths.DCF_DEICES not in self.rdb:
            self.rdb[paths.DCF_DEVICES] = self.__get_devices()

        self.all_devices_model.model_data = self.rdb[paths.DCF_DEVICES]
        self.selected_devices_model.model_dat = self.rdb[paths.BCF_DEV_MIPI(
            current_revision)]

    def __get_devices(self):
        items = common.get_device_names_in_customer_path()
        items.sort()
        data = []
        for item in items:
            row = self.__get_row_data(item)
            if row:
                data.append(row)
        return data

    def __get_row_data(self, device_name):
        """Returns row data for the selected device"""
