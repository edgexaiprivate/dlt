a = [0,1,2,3,4,6]

def checkdup(a):
    set_a = set(a)
    return 'Np DUplicates' if len(a) == len(set_a) else 'DUplicates'

print(checkdup(a))

{
  "restaurant": {
    "id": 1,
    "name": "Hotel Saravana Bhavan",
    "slug": "hotel-saravana",
    "logo_url": null,
    "is_active": true,
    "created_at": "2026-05-26T18:21:27.875998Z"
  },
  "groups": [
    {
      "id": 1,
      "restaurant_id": 1,
      "name": "South Indian",
      "name_local": "தென்னிந்திய உணவு",
      "instruction": "Pure Veg | GST Included",
      "sequence": 1,
      "is_active": true,
      "image_url": null,
      "created_at": "2026-05-26T18:21:28.516246Z",
      "sub_groups": [
        {
          "id": 1,
          "group_id": 1,
          "name": "Dosa",
          "name_local": null,
          "sequence": 1,
          "is_active": true,
          "created_at": "2026-05-26T18:21:28.541134Z",
          "items": [
            {
              "id": 1,
              "sub_group_id": 1,
              "name": "Plain Dosa",
              "name_local": null,
              "description": null,
              "price": 60,
              "image_url": null,
              "status": "not_available",
              "is_veg": true,
              "sequence": 1,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.560886Z",
              "updated_at": "2026-06-09T13:25:52.744464Z"
            },
            {
              "id": 2,
              "sub_group_id": 1,
              "name": "Masala Dosa",
              "name_local": "ಬನ್ಸ್ ",
              "description": null,
              "price": 80555,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 2,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.560911Z",
              "updated_at": "2026-06-09T15:54:59.672596Z"
            },
            {
              "id": 3,
              "sub_group_id": 1,
              "name": "Ghee Roast Dosa",
              "name_local": null,
              "description": null,
              "price": 10,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 3,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.560919Z",
              "updated_at": "2026-06-09T10:25:36.916169Z"
            },
            {
              "id": 4,
              "sub_group_id": 1,
              "name": "Paper Dosa",
              "name_local": null,
              "description": null,
              "price": 70,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 4,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.560926Z",
              "updated_at": "2026-06-09T10:27:42.144715Z"
            },
            {
              "id": 5,
              "sub_group_id": 1,
              "name": "Set Dosa",
              "name_local": null,
              "description": null,
              "price": 70,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 5,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.560934Z",
              "updated_at": "2026-05-26T18:21:28.560939Z"
            }
          ]
        },
        {
          "id": 2,
          "group_id": 1,
          "name": "Idli",
          "name_local": null,
          "sequence": 2,
          "is_active": true,
          "created_at": "2026-05-26T18:21:28.551910Z",
          "items": [
            {
              "id": 6,
              "sub_group_id": 2,
              "name": "Plain Idli (2 pcs)",
              "name_local": null,
              "description": null,
              "price": 50,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 1,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.605159Z",
              "updated_at": "2026-05-26T18:21:28.605170Z"
            },
            {
              "id": 7,
              "sub_group_id": 2,
              "name": "Ghee Idli",
              "name_local": null,
              "description": null,
              "price": 65,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 2,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.605174Z",
              "updated_at": "2026-05-26T18:21:28.605177Z"
            },
            {
              "id": 8,
              "sub_group_id": 2,
              "name": "Sambar Idli",
              "name_local": null,
              "description": null,
              "price": 70,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 3,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.605181Z",
              "updated_at": "2026-05-26T18:21:28.605185Z"
            }
          ]
        },
        {
          "id": 3,
          "group_id": 1,
          "name": "Pongal & Upma",
          "name_local": null,
          "sequence": 3,
          "is_active": true,
          "created_at": "2026-05-26T18:21:28.600167Z",
          "items": [
            {
              "id": 9,
              "sub_group_id": 3,
              "name": "Ven Pongal",
              "name_local": null,
              "description": null,
              "price": 70,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 1,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.620875Z",
              "updated_at": "2026-05-26T18:21:28.620880Z"
            },
            {
              "id": 10,
              "sub_group_id": 3,
              "name": "Khara Bath",
              "name_local": null,
              "description": null,
              "price": 65,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 2,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.620883Z",
              "updated_at": "2026-05-26T18:21:28.620885Z"
            },
            {
              "id": 11,
              "sub_group_id": 3,
              "name": "Kesari Bath",
              "name_local": null,
              "description": null,
              "price": 55,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 3,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.620886Z",
              "updated_at": "2026-05-26T18:21:28.620888Z"
            }
          ]
        }
      ]
    },
    {
      "id": 2,
      "restaurant_id": 1,
      "name": "Beverages",
      "name_local": "பானங்கள்",
      "instruction": "Fresh & Hot",
      "sequence": 2,
      "is_active": true,
      "image_url": null,
      "created_at": "2026-05-26T18:21:28.616675Z",
      "sub_groups": [
        {
          "id": 4,
          "group_id": 2,
          "name": "Tea & Coffee",
          "name_local": null,
          "sequence": 1,
          "is_active": true,
          "created_at": "2026-05-26T18:21:28.627128Z",
          "items": [
            {
              "id": 12,
              "sub_group_id": 4,
              "name": "Filter Coffee",
              "name_local": null,
              "description": null,
              "price": 35,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 1,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.636914Z",
              "updated_at": "2026-05-26T18:21:28.636920Z"
            },
            {
              "id": 13,
              "sub_group_id": 4,
              "name": "Tea",
              "name_local": null,
              "description": null,
              "price": 25,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 2,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.636923Z",
              "updated_at": "2026-05-26T18:21:28.636925Z"
            },
            {
              "id": 14,
              "sub_group_id": 4,
              "name": "Bru Coffee",
              "name_local": null,
              "description": null,
              "price": 30,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 3,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.636926Z",
              "updated_at": "2026-05-26T18:21:28.636928Z"
            }
          ]
        },
        {
          "id": 5,
          "group_id": 2,
          "name": "Cold Drinks",
          "name_local": null,
          "sequence": 2,
          "is_active": true,
          "created_at": "2026-05-26T18:21:28.633066Z",
          "items": [
            {
              "id": 15,
              "sub_group_id": 5,
              "name": "Fresh Lime Soda",
              "name_local": null,
              "description": null,
              "price": 60,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 1,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.648175Z",
              "updated_at": "2026-05-26T18:21:28.648182Z"
            },
            {
              "id": 16,
              "sub_group_id": 5,
              "name": "Buttermilk",
              "name_local": null,
              "description": null,
              "price": 30,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 2,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.648185Z",
              "updated_at": "2026-05-26T18:21:28.648187Z"
            },
            {
              "id": 17,
              "sub_group_id": 5,
              "name": "Lassi",
              "name_local": null,
              "description": null,
              "price": 70,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 3,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.648189Z",
              "updated_at": "2026-05-26T18:21:28.648190Z"
            }
          ]
        }
      ]
    },
    {
      "id": 3,
      "restaurant_id": 1,
      "name": "North Indian",
      "name_local": "उत्तर भारतीय",
      "instruction": "Chef's Special",
      "sequence": 3,
      "is_active": true,
      "image_url": null,
      "created_at": "2026-05-26T18:21:28.643575Z",
      "sub_groups": [
        {
          "id": 6,
          "group_id": 3,
          "name": "Breads",
          "name_local": null,
          "sequence": 1,
          "is_active": true,
          "created_at": "2026-05-26T18:21:28.653967Z",
          "items": [
            {
              "id": 18,
              "sub_group_id": 6,
              "name": "Chapati",
              "name_local": null,
              "description": null,
              "price": 15,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 1,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.660826Z",
              "updated_at": "2026-05-26T18:21:28.660832Z"
            },
            {
              "id": 19,
              "sub_group_id": 6,
              "name": "Paratha",
              "name_local": null,
              "description": null,
              "price": 60,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 2,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.660835Z",
              "updated_at": "2026-05-26T18:21:28.660837Z"
            },
            {
              "id": 20,
              "sub_group_id": 6,
              "name": "Puri Bhaji",
              "name_local": null,
              "description": null,
              "price": 80,
              "image_url": null,
              "status": "available",
              "is_veg": true,
              "sequence": 3,
              "session": "all_day",
              "created_at": "2026-05-26T18:21:28.660838Z",
              "updated_at": "2026-05-26T18:21:28.660840Z"
            }
          ]
        }
      ]
    }
  ],
  "published_at": "2026-06-10T02:53:27.514505Z"
}



@router.get("/restaurant/{restaurant_id}", response_model=List[TemplateOut])
async def list_templates(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_restaurant(current_user, restaurant_id)

    result = await db.execute(
        select(Menutemplates)
        .where(Menutemplates.restaurant_id == restaurant_id)
        .options(
            selectinload(Menutemplates.items).selectinload(MenutemplatesItems.menu_item)
        )
        .order_by(Menutemplates.id)
    )
    templates = result.scalars().all()
    return [TemplateOut.model_validate(t) for t in templates]


# ─── Create / Save a template with items ─────────────────────────────────────

@router.post("/restaurant/{restaurant_id}", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template(
    restaurant_id: int,
    body: TemplateSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    _assert_restaurant(current_user, restaurant_id)

    # Validate all item IDs exist
    if body.items:
        item_ids = [i.item_id for i in body.items]
        result = await db.execute(
            select(MenuItem).where(MenuItem.id.in_(item_ids))
        )
        found = {m.id for m in result.scalars().all()}
        missing = set(item_ids) - found
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Menu items not found: {sorted(missing)}"
            )

    # Create template
    template = Menutemplates(
        restaurant_id=restaurant_id,
        name=body.name,
        name_local=body.name_local,
        price=0.0,
        is_active=False,
    )
    db.add(template)
    await db.flush()  # get template.id before adding children

    # Add template items
    for entry in body.items:
        db.add(MenutemplatesItems(
            template_id=template.id,
            items_id=entry.item_id,
            duration_second=entry.duration_seconds,
        ))

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Menutemplates)
        .where(Menutemplates.id == template.id)
        .options(
            selectinload(Menutemplates.items).selectinload(MenutemplatesItems.menu_item)
        )
    )
    template = result.scalar_one()
    return TemplateOut.model_validate(template)

