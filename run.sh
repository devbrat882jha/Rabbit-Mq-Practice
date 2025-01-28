#!/bin/bash

# Start all consumers
python -m consumers.email_consumer &
python -m consumers.inventory_consumer &
python -m consumers.stock_update &
python -m consumers.shipment_consumer &
wait

