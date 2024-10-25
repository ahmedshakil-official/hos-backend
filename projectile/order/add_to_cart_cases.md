1. get stock and product from stock ID/alias
2. create or get cart for the request user, user will have two cart `regular` and `pre_order`
3. prepare data for cart_item model which we got from `step 1`
    -
4. need to check
 - order mode
 - minimum_order_limit
 - order_limit_per_day (Uttara, Mirpur)

5. calculate amount based on the discount factors
 - round_discount